"""
Part 3 — the full API + UI + mobile + tenant-isolation scenario, described
in docs/case-study-solution.md (Section 4) and docs/test-plan.md.

Implemented as three independent tests sharing the same `created_project`
fixture rather than one monolithic test function, so a mobile-specific
failure (e.g. a BrowserStack device temporarily unavailable) doesn't
prevent the API/UI and tenant-isolation checks from running and reporting
their own pass/fail. The single-flow version the case study describes:

    def test_project_creation_flow():
        project = create_project_via_api()
        verify_project_in_web_ui(project)
        verify_project_on_mobile(project)
        verify_tenant_isolation(project)

...is represented here as the three test methods below, all consuming
`created_project`. See docs/testing-approach.md for the full rationale.
"""
import pytest
from playwright.sync_api import expect
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def _login_web(page, base_url, email, password):
    page.goto(f"{base_url}/login", wait_until="domcontentloaded")
    expect(page.locator("#email")).to_be_visible()
    page.fill("#email", email)
    page.fill("#password", password)
    page.click("#login-btn")
    page.wait_for_url("**/dashboard", timeout=15000)


class TestProjectCreationFlow:
    def test_project_creation_flow(self, created_project, page, base_url, test_users):
        # 1. API: project already created via the created_project fixture.
        assert created_project["status"] == "active"

        # 2. Web UI: verify it appears for the owning tenant.
        admin = test_users["company1_admin"]
        _login_web(page, base_url, admin["email"], admin["password"])
        page.goto(f"{base_url}/projects", wait_until="domcontentloaded")
        expect(page.locator("[data-testid='project-list']")).to_be_visible(timeout=15000)

        card = page.locator(f"[data-testid='project-card-{created_project['id']}']")
        expect(card).to_be_visible(timeout=15000)
        expect(card).to_contain_text(created_project["name"])

    @pytest.mark.mobile
    def test_mobile_accessibility(self, created_project, base_url, test_users, browserstack_hub):
        # 3. Mobile: verified via BrowserStack (Automate for mobile web; a
        # native app would swap this for App Automate + Appium — see the
        # Playwright-vs-Selenium note in docs/testing-approach.md).
        capabilities = {
            "bstack:options": {
                "deviceName": "iPhone 14",
                "osVersion": "16",
                "realMobile": "true",
                "projectName": "WorkFlow Pro QA",
                "buildName": "project-creation-flow",
                "sessionName": "mobile-accessibility-check",
            },
            "browserName": "safari",
        }
        admin = test_users["company1_admin"]
        driver = webdriver.Remote(command_executor=browserstack_hub, desired_capabilities=capabilities)
        try:
            driver.get(f"{base_url}/login")
            driver.find_element(By.ID, "email").send_keys(admin["email"])
            driver.find_element(By.ID, "password").send_keys(admin["password"])
            driver.find_element(By.ID, "login-btn").click()

            WebDriverWait(driver, 15).until(EC.url_contains("/dashboard"))
            driver.get(f"{base_url}/projects")

            card = WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, f"[data-testid='project-card-{created_project['id']}']")
                )
            )
            assert created_project["name"] in card.text
        finally:
            driver.quit()

    @pytest.mark.security
    def test_tenant_isolation(self, created_project, company2_client, page, base_url, test_users):
        project_id = created_project["id"]

        # Check #1 (API layer): company2's token must not read a company1
        # project, even by guessing/enumerating the numeric id.
        resp = company2_client.get_project(project_id)
        assert resp.status_code in (403, 404), (
            f"Tenant isolation failure: company2 API token could read company1 "
            f"project {project_id} (status {resp.status_code})"
        )

        # Check #2 (UI list layer): a permissive frontend could still leak
        # data even if the API is correctly locked down, so check both.
        user = test_users["company2_user"]
        _login_web(page, base_url, user["email"], user["password"])
        page.goto(f"{base_url}/projects", wait_until="domcontentloaded")
        expect(page.locator(f"[data-testid='project-card-{project_id}']")).to_have_count(0)

        # Check #3 (direct URL navigation): hiding a project from the list
        # view isn't sufficient if /projects/{id} still renders it directly
        # for a company2 session — the check most likely to be skipped, and
        # the one most likely to reveal a real authorization gap.
        response = page.goto(f"{base_url}/projects/{project_id}", wait_until="domcontentloaded")
        assert response.status in (403, 404), (
            f"Tenant isolation failure: direct navigation to /projects/{project_id} "
            f"returned {response.status} for a company2 session"
        )
