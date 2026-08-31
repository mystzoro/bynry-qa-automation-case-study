# Test Plan — WorkFlow Pro (Bynry Case Study)

## Scope

In scope:
- Login and authentication, including 2FA
- Project creation (API) and its reflection in the web UI and mobile web
- Project visibility and multi-tenant isolation
- Cross-browser coverage (Chrome, Firefox, Safari) and mobile devices via
  BrowserStack

Out of scope for this exercise (see `testing-approach.md` for the open
questions behind these):
- Native mobile app testing (assumed responsive web app unless told
  otherwise)
- Performance/load testing
- Third-party integrations beyond what the case study describes

## Test types

| Test type | Tool |
|---|---|
| UI | Playwright |
| API | pytest + `requests` |
| Mobile | BrowserStack + Selenium/Appium concepts |
| Integration (API + UI + mobile) | pytest, combining the above |
| Cross-browser | Playwright (Chromium/Firefox local) + BrowserStack (real Safari) |
| Security / tenant isolation | API response codes + UI + direct URL navigation |

## Priority

**P0 — must pass before any release**
- Login (all supported auth paths, including 2FA)
- Authentication token/session handling
- Tenant isolation (API, UI, and direct URL — a single missed layer is a
  security incident, not a UI bug)

**P1 — high priority, blocks most merges**
- Project creation (API) and its correct reflection in the UI
- Project visibility rules
- Role-based permissions (Admin / Manager / Employee)

**P2 — important, not release-blocking on its own**
- UI/responsive edge cases
- Non-critical-path cross-browser visual differences

## Test data

Generated per-run via the `project_payload` / `run_id` fixtures in the
root `conftest.py`, so parallel runs and repeated CI executions never
collide on the same project name. See `data/test_projects.example.json`
for the shape and `docs/case-study-solution.md` (Section 3.5) for the
full strategy, including cleanup.

## Environments

Assumed: a shared staging environment reachable by both the CI runner and
BrowserStack's cloud. See `docs/testing-approach.md` for the full list of
environment-related assumptions and the questions I'd confirm with the
team before this became a permanent setup.

## Mapping to this repo

| Test plan area | Where it's implemented |
|---|---|
| Flaky login / 2FA | `tests/part1/test_login.py` |
| API-only checks | `tests/api/test_projects_api.py` |
| Web UI checks | `tests/web/test_project_ui.py` |
| Mobile checks | `tests/mobile/test_mobile_project.py` |
| Full integration + tenant isolation | `tests/integration/test_project_creation_flow.py` |
