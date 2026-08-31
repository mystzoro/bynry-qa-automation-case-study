"""
Direct API-layer tests for the Projects endpoint (a Part 3 building block),
independent of any UI. Uses the shared fixtures from the root conftest.py,
so API behavior is covered on its own — not only as a side effect of the
full integration test in tests/integration/.
"""


def test_create_project_returns_active_status(created_project):
    assert created_project["status"] == "active"
    assert created_project["id"] is not None


def test_created_project_is_readable_by_owning_tenant(created_project, company1_client):
    resp = company1_client.get_project(created_project["id"])
    assert resp.status_code == 200
    assert resp.json()["name"] == created_project["name"]


def test_project_not_readable_by_other_tenant(created_project, company2_client):
    # API-layer half of tenant isolation — also verified end-to-end in
    # tests/integration/test_project_creation_flow.py alongside the UI and
    # direct-URL checks.
    resp = company2_client.get_project(created_project["id"])
    assert resp.status_code in (403, 404), (
        f"Tenant isolation failure: company2 API token could read company1 "
        f"project {created_project['id']} (status {resp.status_code})"
    )
