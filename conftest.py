"""
Shared pytest configuration and fixtures for the Bynry QA automation case
study repo.

Individual test modules stay self-contained wherever practical (each one
can be read on its own). Only the genuinely cross-cutting pieces live here:
the API client, tenant/test-account configuration, generated test data, and
a small extension of pytest-playwright's own fixtures.

See docs/case-study-solution.md for the reasoning behind these choices and
docs/testing-approach.md for assumptions.
"""
import os
import time
import uuid

import pytest
import requests
from dotenv import load_dotenv

load_dotenv()

_BASE_URL = os.environ.get("WORKFLOWPRO_BASE_URL", "https://app.workflowpro.com")
_BASE_API_URL = os.environ.get("WORKFLOWPRO_API_URL", "https://api.workflowpro.com")
_BROWSERSTACK_USERNAME = os.environ.get("BROWSERSTACK_USERNAME", "")
_BROWSERSTACK_ACCESS_KEY = os.environ.get("BROWSERSTACK_ACCESS_KEY", "")
_BROWSERSTACK_HUB = (
    f"https://{_BROWSERSTACK_USERNAME}:{_BROWSERSTACK_ACCESS_KEY}"
    f"@hub-cloud.browserstack.com/wd/hub"
)

# Test accounts declare their own auth shape explicitly instead of having
# 2FA detected at runtime via a timeout (see docs/testing-approach.md).
_TEST_USERS = {
    "company1_admin": {
        "email": os.environ.get("COMPANY1_ADMIN_EMAIL", "company1-admin@example.com"),
        "password": os.environ.get("COMPANY1_ADMIN_PASSWORD", ""),
        "requires_2fa": False,
    },
    "company2_user": {
        "email": os.environ.get("COMPANY2_USER_EMAIL", "company2-user@example.com"),
        "password": os.environ.get("COMPANY2_USER_PASSWORD", ""),
        "requires_2fa": True,
    },
}

_TENANTS = {
    "company1": {"tenant_id": "company1", "token": os.environ.get("COMPANY1_API_TOKEN", "")},
    "company2": {"tenant_id": "company2", "token": os.environ.get("COMPANY2_API_TOKEN", "")},
}


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    # Extends pytest-playwright's own fixture rather than replacing it, so
    # its --browser / --headed / --device CLI flags keep working.
    return {**browser_context_args, "viewport": {"width": 1440, "height": 900}}


@pytest.fixture(scope="session")
def base_url():
    return _BASE_URL


@pytest.fixture(scope="session")
def base_api_url():
    return _BASE_API_URL


@pytest.fixture(scope="session")
def browserstack_hub():
    return _BROWSERSTACK_HUB


@pytest.fixture(scope="session")
def test_users():
    return _TEST_USERS


@pytest.fixture(scope="session")
def otp_code():
    return os.environ.get("TEST_OTP_CODE", "")


class ProjectAPIClient:
    """Centralizes auth headers, retries and tenant scoping for the Projects API."""

    def __init__(self, tenant_id: str, token: str, base_api_url: str = _BASE_API_URL):
        self.base_api_url = base_api_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": tenant_id,
                "Content-Type": "application/json",
            }
        )

    def create_project(self, name, description="", team_members=None, retries=3):
        payload = {"name": name, "description": description, "team_members": team_members or []}
        last_error = None
        for attempt in range(retries):
            try:
                resp = self.session.post(f"{self.base_api_url}/api/v1/projects", json=payload, timeout=10)
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as e:
                last_error = e
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # backoff, only before a retry actually happens
        # Outside the for-loop entirely: reached only once every attempt is
        # exhausted, so a single dropped connection doesn't abort early.
        raise RuntimeError(f"Failed to create project after {retries} attempts: {last_error}")

    def get_project(self, project_id):
        return self.session.get(f"{self.base_api_url}/api/v1/projects/{project_id}", timeout=10)

    def delete_project(self, project_id):
        # Best-effort cleanup — a flaky teardown shouldn't fail the test itself.
        try:
            self.session.delete(f"{self.base_api_url}/api/v1/projects/{project_id}", timeout=10)
        except requests.RequestException as e:
            print(f"WARN: cleanup failed for project {project_id}: {e}")


@pytest.fixture
def run_id():
    return uuid.uuid4().hex[:8]


@pytest.fixture
def project_payload(run_id):
    # Unique per run so parallel workers / repeated CI runs never collide on name.
    return {
        "name": f"QA Integration Test Project {run_id}",
        "description": "Created by automated integration test — safe to delete.",
        "team_members": ["qa.bot@company1.com"],
    }


@pytest.fixture
def company1_client():
    return ProjectAPIClient(**_TENANTS["company1"])


@pytest.fixture
def company2_client():
    return ProjectAPIClient(**_TENANTS["company2"])


@pytest.fixture
def created_project(company1_client, project_payload):
    project = company1_client.create_project(**project_payload)
    yield project
    company1_client.delete_project(project["id"])  # always runs, pass or fail
