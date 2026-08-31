"""
Mobile verification via BrowserStack (Part 3).

Uses Selenium against BrowserStack's hub rather than Playwright — a
deliberate choice, not an inconsistency with the Playwright-based web
tests. See docs/testing-approach.md for the reasoning. In a fuller
framework this would sit behind a DriverFactory so tests don't know which
underlying driver a given platform uses (docs/case-study-solution.md,
Section 3.3).

Assumes "mobile" means the responsive web app in a real-device mobile
browser (BrowserStack Automate). A native app would use BrowserStack App
Automate + Appium against an uploaded build instead.
"""
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@pytest.mark.mobile
def test_project_accessible_on_mobile(created_project, base_url, test_users, browserstack_hub):
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
        driver.quit()  # release the BrowserStack session whether we passed or failed
