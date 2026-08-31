"""
Web UI verification for project creation (Part 3). The API creates the
project as the source of truth (see the `created_project` fixture in the
root conftest.py); this test only observes that state through the web UI.
"""
from playwright.sync_api import expect


def _login_web(page, base_url, email, password):
    page.goto(f"{base_url}/login", wait_until="domcontentloaded")
    expect(page.locator("#email")).to_be_visible()
    page.fill("#email", email)
    page.fill("#password", password)
    page.click("#login-btn")
    page.wait_for_url("**/dashboard", timeout=15000)


def test_project_appears_in_web_ui(created_project, page, base_url, test_users):
    admin = test_users["company1_admin"]
    _login_web(page, base_url, admin["email"], admin["password"])

    page.goto(f"{base_url}/projects", wait_until="domcontentloaded")
    expect(page.locator("[data-testid='project-list']")).to_be_visible(timeout=15000)

    card = page.locator(f"[data-testid='project-card-{created_project['id']}']")
    expect(card).to_be_visible(timeout=15000)  # tolerates async list rendering
    expect(card).to_contain_text(created_project["name"])
