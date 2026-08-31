"""
Part 1 — corrected flaky-test implementation.

The original problems and reasoning are documented in
docs/case-study-solution.md (Section 2). Key changes here: deterministic
per-account 2FA handling (no timeout-based guessing), application-state
waits (domcontentloaded + expect()) instead of networkidle or one-shot
is_visible() checks, and pytest-playwright's own per-test context isolation
instead of a hand-rolled browser/page fixture.
"""
import re

from playwright.sync_api import expect


def login(page, base_url, email, password, requires_2fa, otp_code):
    # domcontentloaded + an explicit visible-element wait, not networkidle:
    # a SaaS app's background polling/analytics/WebSocket traffic means the
    # network may never go fully idle even once the login form is ready.
    page.goto(f"{base_url}/login", wait_until="domcontentloaded")
    expect(page.locator("#email")).to_be_visible()

    page.fill("#email", email)
    page.fill("#password", password)
    page.click("#login-btn")

    # Deterministic, not timeout-based: the account itself declares whether
    # a 2FA step is expected, so a slow OTP screen and a genuinely missing
    # one are never confused with each other.
    if requires_2fa:
        expect(page.locator("#otp-code")).to_be_visible(timeout=10000)
        page.fill("#otp-code", otp_code)
        page.click("#otp-submit-btn")

    # Wait for the real navigation event rather than racing a URL string compare.
    page.wait_for_url(re.compile(r".*/dashboard"), timeout=15000)


def test_user_login(page, base_url, test_users, otp_code):
    user = test_users["company1_admin"]
    login(page, base_url, user["email"], user["password"], user["requires_2fa"], otp_code)

    # expect() polls/retries until it passes or times out, which is what
    # fixes the race between "URL changed" and "dashboard actually rendered".
    expect(page).to_have_url(re.compile(r".*/dashboard"))
    expect(page.locator(".welcome-message")).to_be_visible(timeout=10000)


def test_multi_tenant_access(page, base_url, test_users, otp_code):
    user = test_users["company2_user"]
    login(page, base_url, user["email"], user["password"], user["requires_2fa"], otp_code)

    # Wait for the list container itself, not just the login redirect —
    # dashboard content loads dynamically and tenants load at different speeds.
    project_list = page.locator("[data-testid='project-list']")
    expect(project_list).to_be_visible()

    projects = page.locator(".project-card")
    expect(projects.first).to_be_visible()  # at least one card has actually rendered
    count = projects.count()
    assert count > 0, "Expected at least one project card to render for company2"

    for i in range(count):
        text = projects.nth(i).text_content()
        assert "Company2" in text, f"Tenant isolation violation: found non-Company2 project: {text}"
