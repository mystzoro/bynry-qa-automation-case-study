# QA Automation Engineering Intern — Case Study Solution

**WorkFlow Pro — Multi-Platform Test Automation**
Prepared for Bynry Inc. · Priyanshu Chand

This is the full write-up for the Bynry QA Automation Engineering Intern
case study. The runnable code this document walks through lives in
`tests/`, `conftest.py`, `config/`, and `data/` at the repo root; this file
is the reasoning and narrative behind it.

## 1. Executive Summary

My approach centers on three principles: deterministic test execution,
separation of concerns, and tenant-aware isolation testing.

For flaky UI tests (Part 1), timing assumptions and one-shot assertions
are replaced with Playwright's auto-retrying `expect()` assertions and
explicit application-state waits rather than network-idle heuristics. Test
credentials and 2FA behavior are made explicit per test account instead of
inferred at runtime, and browser/context fixtures guarantee isolation
between tests.

For the framework (Part 2), UI page objects, API clients, test-data
factories, and tenant/environment/browser configuration are kept in
separate layers connected through composable pytest fixtures, so the
framework can scale across the environment × tenant × role × platform
matrix without a rigid inheritance hierarchy.

For end-to-end validation (Part 3), API-created data is treated as the
source of truth and verified as a read-only observer through the web and
mobile layers. Tenant isolation is checked independently at three points —
the API layer, the UI list layer, and direct URL navigation — since any
one of the three could pass while the others quietly leak data.

## 2. Part 1 — Debugging Flaky Test Code

### 2.1 Flakiness issues — summary

| Issue | Root cause | Fix |
|---|---|---|
| Dynamic dashboard loading | Elements render asynchronously after navigation | `expect().to_be_visible()` polling assertions |
| Login → dashboard redirect | SPA client-side routing races a URL string check | `wait_for_url()` / `expect(page).to_have_url()` |
| 2FA for some accounts | Treated as universal, or ignored entirely | Per-account `requires_2fa` flag, explicit branch |
| Hardcoded credentials | Static secrets committed in source | Env vars from the CI secret store |
| Shared account across parallel workers | No per-test isolation | Isolated browser context per test via fixtures |
| Tenant-dependent load times | Fixed timeouts / one-shot boolean checks | Locator-based waits with generous, tenant-aware timeouts |
| Browser cleanup on failure | `close()` skipped when an assertion raises | Fixture teardown (`yield` + close) runs regardless of outcome |
| No failure diagnostics | Nothing captured when CI fails intermittently | Trace/screenshot/console log capture on failure (Section 5) |

### 2.2 Full list of issues identified, with reasoning

1. No wait for the page/app to actually be ready before interacting with
   it. `page.fill()` and `page.click()` run the instant Playwright's
   default navigation wait resolves, which is often before the
   single-page app has hydrated its event handlers.
2. `page.click("#login-btn")` doesn't wait for anything to happen
   afterward — the test immediately races ahead to the assertions while
   the login request is still in flight.
3. `assert page.url == "..."` is evaluated at the exact instant execution
   reaches that line. In an SPA, the visible URL frequently changes via
   client-side routing slightly before (or after) the corresponding view
   has actually mounted, so this is a coin flip under load.
4. `page.locator(".welcome-message").is_visible()` returns a one-time
   snapshot boolean — it does not retry. If that element renders 200ms
   after the check runs, the test sees "not visible" and fails even
   though the page is working correctly.
5. 2FA is not handled at all. The additional context states some users
   require 2FA; for those accounts the test will stall waiting for a
   dashboard redirect that never comes, and for accounts whose
   2FA/"trusted device" state can flip, the same test flips between pass
   and fail.
6. Credentials are hardcoded in source (`admin@company1.com` /
   `password123`). Besides being a secrets-hygiene problem, it means test
   data lives in one more place that has to be kept in sync with whatever
   the real seeded accounts are.
7. No test isolation between runs or parallel workers. Both tests
   implicitly depend on specific shared accounts; if CI runs tests in
   parallel (pytest-xdist, multiple BrowserStack sessions, etc.), two
   workers can log in as the same user at the same time and stomp on each
   other's session/cookies.
8. `browser.close()` only executes on the happy path. If any assertion
   above it raises, execution jumps past `browser.close()` before the
   `with` block exits, which can leak Chromium processes across a long CI
   test suite and eventually causes resource-exhaustion failures that look
   unrelated to the actual bug.
9. `page.locator(".project-card").all()` captures whatever is in the DOM
   at that instant. Because the prompt says dashboard elements load
   dynamically and different tenants load at different speeds, this can
   read 0 or a partial list on a slow tenant while a fast tenant's test
   passes every time.
10. No explicit viewport, browser engine, or timeout configuration. CI
    matrices commonly vary screen size and browser (Chromium/Firefox/
    WebKit), which changes rendering timing and can hide or reveal
    elements differently than a developer's local Chrome window.
11. No diagnostics on failure — no screenshot, no trace, no
    console/network log capture — so an intermittent CI failure is
    expensive to root-cause after the run has ended.

### 2.3 Why these surface more in CI/CD than locally

- CI runners are shared, resource-constrained containers/VMs — slower
  CPU and memory pressure stretch out JS hydration and rendering time
  that a developer's laptop absorbs without issue.
- CI most commonly runs headless, and often runs several jobs in
  parallel on the same host, adding CPU contention that turns "basically
  instant" DOM updates into a race.
- Network path from the CI runner to the app (often crossing a public
  cloud region to reach a staging environment) has higher and more
  variable latency than a local machine hitting a nearby or
  already-warm environment.
- CI matrices intentionally vary browser engine and screen size (per the
  prompt) — Chromium, Firefox and WebKit differ in paint/hydration
  timing, and different viewports change what's visible without scroll
  (e.g., whether the welcome banner is above the fold).
- Parallel execution in CI is exactly what exposes shared-state bugs
  like two workers reusing the same login account — a single sequential
  local run rarely triggers that collision.
- CI typically points at a shared staging environment under real
  multi-tenant load, so the tenant-dependent loading-time variance
  called out in the prompt is far more pronounced than against a quiet
  local/staging instance.

### 2.4 Corrected implementation

Two deliberate choices beyond the obvious fixture/`expect()` cleanup:
(1) waits are anchored to application state (a specific locator becoming
visible), not to `networkidle` — a modern SaaS app runs analytics
beacons, WebSockets, and polling requests that never let the network
truly go idle, so `networkidle` is itself an unreliable signal.
(2) 2FA is resolved deterministically per test account (a `requires_2fa`
flag on the account) rather than inferred from whether an OTP field
appears within a timeout — a slow-loading 2FA screen and a genuinely
absent one would otherwise be indistinguishable.

See [`tests/part1/test_login.py`](../tests/part1/test_login.py) for the
runnable version. Reproduced here for reference:

```python
import re
from playwright.sync_api import expect


def login(page, base_url, email, password, requires_2fa, otp_code):
    page.goto(f"{base_url}/login", wait_until="domcontentloaded")
    expect(page.locator("#email")).to_be_visible()

    page.fill("#email", email)
    page.fill("#password", password)
    page.click("#login-btn")

    if requires_2fa:
        expect(page.locator("#otp-code")).to_be_visible(timeout=10000)
        page.fill("#otp-code", otp_code)
        page.click("#otp-submit-btn")

    page.wait_for_url(re.compile(r".*/dashboard"), timeout=15000)


def test_user_login(page, base_url, test_users, otp_code):
    user = test_users["company1_admin"]
    login(page, base_url, user["email"], user["password"], user["requires_2fa"], otp_code)
    expect(page).to_have_url(re.compile(r".*/dashboard"))
    expect(page.locator(".welcome-message")).to_be_visible(timeout=10000)


def test_multi_tenant_access(page, base_url, test_users, otp_code):
    user = test_users["company2_user"]
    login(page, base_url, user["email"], user["password"], user["requires_2fa"], otp_code)

    project_list = page.locator("[data-testid='project-list']")
    expect(project_list).to_be_visible()

    projects = page.locator(".project-card")
    expect(projects.first).to_be_visible()
    count = projects.count()
    assert count > 0, "Expected at least one project card to render for company2"

    for i in range(count):
        text = projects.nth(i).text_content()
        assert "Company2" in text, f"Tenant isolation violation: found non-Company2 project: {text}"
```

### 2.5 Reliability strategy

The underlying rule across all of the above: **wait for application
state, not for time or network activity.** Every wait in the corrected
version is tied to something the app itself exposes (a locator becoming
visible, a URL actually changing, an account's declared auth shape)
rather than a fixed sleep, a `networkidle` heuristic, or an inferred
timeout. Combined with per-test browser-context isolation and
CI-secret-backed credentials, this removes the shared-state and timing
assumptions that caused the original flakiness, and it degrades
gracefully: a genuinely slow tenant gets more time via the same locator
wait, instead of needing a different code path.

## 3. Part 2 — Automation Framework Design

### 3.1 Architecture

The framework separates four concerns that otherwise tend to tangle
together in ad-hoc automation: how to interact with the UI (page
objects), how to interact with the API (API clients), what data a test
needs (factories/fixtures), and where/who/what a test runs against
(environment, tenant, role, and browser/device configuration). Each
concern is independently parametrizable through pytest fixtures, so
adding a fourth tenant or a new user role doesn't require touching page
objects or API clients at all.

### 3.2 Folder structure

The layout below is the "fully layered" version of the framework this
case study describes at design level; the actual runnable repo
(`tests/`, `conftest.py`, `config/`, `data/`) is a leaner instance of the
same separation of concerns, sized for a take-home assessment rather
than a multi-year production codebase.

```text
workflowpro-qa/
├── config/
│   ├── environments/
│   │   ├── dev.yaml
│   │   ├── staging.yaml
│   │   └── prod.yaml
│   ├── tenants.yaml            # per-tenant subdomains, role -> test-account mapping
│   └── browserstack.yaml       # browser/device capability matrix (single source of truth)
├── core/
│   ├── driver_factory.py       # builds Playwright browser/context OR BrowserStack remote driver
│   ├── api_client.py           # BaseAPIClient: auth headers, retries, logging
│   ├── base_page.py            # BasePage: shared wait helpers for Playwright page objects
│   └── tenant_context.py       # TenantContext dataclass: tenant_id, base_url, seeded users
├── pages/
│   ├── web/
│   │   ├── login_page.py
│   │   ├── dashboard_page.py
│   │   └── project_page.py
│   └── mobile/
│       ├── login_screen.py
│       └── dashboard_screen.py
├── api/
│   ├── endpoints/
│   │   └── projects.py
│   └── schemas/
│       └── project_schema.py   # response validation (pydantic/jsonschema)
├── data/
│   ├── factories/
│   │   └── project_factory.py  # generates uniquely-named test entities
│   └── fixtures/
├── tests/
│   ├── web/
│   ├── mobile/
│   ├── api/
│   └── integration/             # cross-layer tests like Part 3
├── utils/
│   ├── wait_helpers.py
│   ├── auth_helpers.py
│   └── retry.py
├── reports/
├── ci/
│   └── pipeline.yml
├── conftest.py
└── pytest.ini
```

### 3.3 Base components

- **BasePage** — Wraps a Playwright `Page` with shared conveniences
  (`safe_click`, `wait_and_fill`, `wait_for_toast`) so every web page
  object gets consistent, auto-retrying interactions instead of each page
  re-implementing waits.
- **BaseAPIClient** — Wraps a `requests`/`httpx` session; injects
  `Authorization` and `X-Tenant-ID` headers, applies retry/backoff for
  transient network errors, and centralizes request/response logging so
  every endpoint client (`ProjectsClient`, `UsersClient`, ...) inherits
  the same reliability behavior. (`conftest.py`'s `ProjectAPIClient` in
  this repo is the concrete, working instance of this idea.)
- **TenantContext** — A small dataclass (tenant_id, subdomain/base_url,
  seeded users per role, expected branding) passed into fixtures so a
  test can be parametrized across tenants without hardcoding URLs or
  accounts inline.
- **DriverFactory** — Given an environment + platform
  (chrome/firefox/webkit/android/ios), returns either a local Playwright
  browser/context or a BrowserStack remote WebDriver built from the
  shared capability matrix — so tests don't know or care whether they're
  running locally or on BrowserStack, or which underlying driver a given
  platform uses.
- **conftest.py fixtures** — Composition over inheritance: environment,
  tenant, role and platform are separate, independently-parametrizable
  fixtures (favoring pytest's fixture graph over a deep `BaseTest` class
  hierarchy, which tends to become rigid as the env × tenant × role ×
  platform matrix grows).

### 3.4 Configuration management

Config is layered so each concern lives in exactly one place and
overrides compose predictably: base defaults < environment overrides
(dev/staging/prod) < tenant overrides < CLI/env-var overrides at run time
(e.g., `pytest --env=staging --tenant=company1 --browser=firefox
--device="iPhone 14"`). Secrets are never stored in these YAML files —
`tenants.yaml` references an env-var name (`COMPANY1_ADMIN_PASSWORD`),
and the actual value is injected by the CI secret store (or a
gitignored `.env.local` for local dev — in this repo, `.env`).

Browser/engine mapping (declared once in `config/browserstack.example.yaml`,
consumed by both local and BrowserStack runs):

- Chromium → Chrome, run locally and via BrowserStack.
- Firefox → Firefox, run locally and via BrowserStack.
- WebKit → fast local signal only. Playwright's WebKit is a different
  build than Apple's Safari/WebKit and is **not** a substitute for real
  Safari coverage.
- BrowserStack real Safari sessions → the actual Safari browser/version,
  used for release-blocking confidence rather than local WebKit.

### 3.5 Test data strategy

Test data uses a factory pattern that generates uniquely-named entities
per run (e.g., `f"QA Test Project {run_id}-{uuid4().hex[:6]}"`), so
parallel workers and repeated CI runs never collide on the same name.
Created entities are torn down via an API-based fixture teardown after
each test (`created_project` in `conftest.py`), with a scheduled nightly
sweep as a safety net for anything orphaned by a crashed run. This is
what separates "I know Playwright" from "I understand automation in a
real, continuously-running company" — data collisions between parallel
runs are one of the most common causes of unrelated-looking CI failures.

### 3.6 Missing requirements — questions I'd ask

1. Test data lifecycle: is there a dedicated, resettable per-tenant
   sandbox, or do we create/delete data against a shared staging
   environment? Is there a seed/reset API we should be using instead of
   ad-hoc API calls from tests?
2. Reporting: is there a required reporting tool (Allure, ReportPortal,
   TestRail) or dashboard, and who consumes results — engineers only, or
   also PMs/support during triage?
3. Parallel execution budget: how many concurrent BrowserStack sessions
   are licensed, and is pytest-xdist-style local parallelism expected as
   well?
4. Flaky-test policy: is there an agreed retry/quarantine mechanism
   (e.g., pytest-rerunfailures) and an owner/process for triaging flaky
   tests before they can block a merge?
5. Environment topology: does CI run against a persistent shared staging
   environment, ephemeral per-PR environments, or a production-adjacent
   canary? This directly changes how aggressive test-data cleanup needs
   to be.
6. Mobile scope: is "mobile" the native app (BrowserStack App Automate +
   Appium, needs a build artifact) or the responsive web app in a mobile
   browser (BrowserStack Automate)? These require materially different
   tooling.
7. 2FA in automation: is there a test-only bypass, a fixed/seeded OTP for
   test accounts, or an API-based token/session injection so most tests
   can skip UI login entirely for speed?
8. Browser/version support matrix: which specific versions (e.g., "last
   2 Chrome versions", "Safari 16+") are officially supported? That
   determines the BrowserStack capability matrix, not just the three
   browser names.
9. Data privacy: can tests use realistic/production-like data, or must
   all test data be fully synthetic, given this is real multi-tenant
   customer data?
10. CI trigger strategy: does the full cross-browser/mobile suite run on
    every PR (cost and time), or is there a fast smoke suite per PR plus
    a full nightly regression?
11. Ownership: who maintains page objects and API clients as the product
    evolves — a dedicated QA team, or feature developers contributing
    test code alongside product code?
12. Non-functional scope: is performance/load testing part of this
    framework's remit (the role description mentions it, this case
    study doesn't), or owned by a separate tool/team?

## 4. Part 3 — API + UI + Mobile Integration Test

### 4.1 Testing strategy

The API creates the source-of-truth project quickly and deterministically;
the web and mobile layers are then verified as read-only observers of that
same state. This keeps the test fast and avoids re-implementing
project-creation logic through three different UIs. Tenant isolation is
checked at three layers on purpose (Section 4.5) because a permissive
frontend or a route-level gap can leak data even when the primary API
check looks correct.

**Why three independent tests, not one monolithic flow.** Rather than a
single `test_project_creation_flow()`, this is implemented as three
independent tests (`test_project_creation_flow`, `test_mobile_accessibility`,
`test_tenant_isolation`) that all consume the same `created_project`
fixture. A mobile-specific failure (e.g., a BrowserStack device
temporarily unavailable) then doesn't prevent the API/UI and
tenant-isolation checks from running and reporting their own pass/fail,
which matters for triage speed on a CI dashboard. The scenario as the case
study frames it, as a single orchestrated flow, would read as:

```python
def test_project_creation_flow():
    project = create_project_via_api()
    verify_project_in_web_ui(project)
    verify_project_on_mobile(project)
    verify_tenant_isolation(project)

# Implemented in tests/integration/ as three independent tests sharing one
# fixture instead, so a failure in one layer doesn't hide or block the
# results of the others.
```

**Why Selenium for the mobile check, when the web layer is Playwright.**
This is a deliberate choice, not an inconsistency: BrowserStack's
real-device mobile support is most mature via Selenium/Appium, whereas
Playwright's own BrowserStack integration is comparatively new and may
not cover every device/OS combination the team needs. The `DriverFactory`
from Section 3.3 is what should hide this from test authors — a test asks
for "iPhone 14 / Safari" and gets back a driver, without needing to know
whether that driver is a Playwright BrowserStack connection or a Selenium
Remote WebDriver underneath.

### 4.2 – 4.5 Implementation

See [`tests/integration/test_project_creation_flow.py`](../tests/integration/test_project_creation_flow.py)
for the runnable version (reproduced in full below), plus
[`tests/api/test_projects_api.py`](../tests/api/test_projects_api.py) and
[`tests/web/test_project_ui.py`](../tests/web/test_project_ui.py) for the
API-only and web-only slices of the same scenario, and
[`tests/mobile/test_mobile_project.py`](../tests/mobile/test_mobile_project.py)
for the mobile-only slice. Shared fixtures (`created_project`,
`company1_client`, `company2_client`, `base_url`, `test_users`,
`browserstack_hub`) live in the root `conftest.py`.

```python
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
        # 3. Mobile: verified via BrowserStack (Automate for mobile web).
        ...  # full implementation in tests/integration/test_project_creation_flow.py

    @pytest.mark.security
    def test_tenant_isolation(self, created_project, company2_client, page, base_url, test_users):
        project_id = created_project["id"]

        # Check #1 (API layer): company2's token must not read a company1 project.
        resp = company2_client.get_project(project_id)
        assert resp.status_code in (403, 404), (
            f"Tenant isolation failure: company2 API token could read company1 "
            f"project {project_id} (status {resp.status_code})"
        )

        # Check #2 (UI list layer): a permissive frontend could still leak data.
        user = test_users["company2_user"]
        _login_web(page, base_url, user["email"], user["password"])
        page.goto(f"{base_url}/projects", wait_until="domcontentloaded")
        expect(page.locator(f"[data-testid='project-card-{project_id}']")).to_have_count(0)

        # Check #3 (direct URL navigation): hiding a project from the list
        # isn't sufficient if /projects/{id} still renders it directly.
        response = page.goto(f"{base_url}/projects/{project_id}", wait_until="domcontentloaded")
        assert response.status in (403, 404), (
            f"Tenant isolation failure: direct navigation to /projects/{project_id} "
            f"returned {response.status} for a company2 session"
        )
```

### 4.6 Test data handling across API/UI

A single `project_payload` fixture generates the project name/description
once per test run (uniqueness via a short UUID suffix), and that same
object is used to create the project through the API and to assert
against in the UI/mobile checks — so the test never re-derives "what the
project should look like" in two places that could drift apart. Cleanup
happens in the `created_project` fixture's teardown (an API `DELETE` call)
so it runs whether the test passes or fails, which keeps the staging
environment from accumulating orphaned "Test Project" rows over time; a
nightly sweep job is the assumed backstop for anything a crashed run
leaves behind.

### 4.7 Cross-platform validation

The same scenario is parametrized across browser targets rather than
assuming Playwright's three engines are a complete substitute for real
browser coverage: Chromium and Firefox map directly to Chrome and
Firefox; Playwright's WebKit gives fast local signal but is not the same
rendering/JS engine as real Safari, so actual Safari coverage runs
through BrowserStack's real Safari sessions (per the
`config/browserstack.example.yaml` matrix in Section 3.4), not local
WebKit. Mobile checks are parametrized over BrowserStack real devices
(e.g., iPhone 14/Safari, Pixel 7/Chrome). Selectors throughout use
`data-testid` attributes rather than CSS classes or visible text, since
those are more likely to change per-browser or per-responsive-layout
than test hooks are.

### 4.8 Tenant isolation

Verified at three independent layers, deliberately not just one: an
API-level check that company2's bearer token gets a 403/404 when it
requests company1's project by id (catches a backend authorization bug
directly); a UI-level check that the same project never appears in
company2's rendered project list (catches a case where the API is
correct but a query/filter bug in the frontend still leaks the row); and
a direct-URL-navigation check that `/projects/{id}` itself returns
403/404 for a company2 session (catches the case where the list view is
correctly filtered but the detail route underneath is not — arguably the
gap most likely to be missed, and the one most likely to reveal a real
authorization bug rather than a UI filtering bug).

### 4.9 Edge cases

- **Network failures:** `ProjectAPIClient` retries transient failures
  with exponential backoff (`2^attempt` seconds, only between attempts)
  before raising, so a single dropped connection to a staging environment
  doesn't fail the whole suite.
- **Slow loading:** all UI/mobile assertions use `expect()`/`WebDriverWait`
  with generous timeouts instead of fixed sleeps or `networkidle`, so a
  slower tenant or a loaded CI runner doesn't turn into a false failure.
- **Mobile responsiveness:** assertions target `data-testid` selectors
  rather than pixel positions or visible-text matching, so layout reflow
  at a smaller viewport doesn't break the check.
- **Cleanup failures:** `delete_project()` catches and logs rather than
  raising, so a flaky teardown call doesn't mask (or get blamed for) a
  real test failure that happened earlier in the same test.
- **Partial data / eventual consistency:** the UI check waits for the
  specific project card by id, not just "any card," so a dashboard that
  streams in projects one at a time doesn't cause a false negative before
  it's done loading.

## 5. CI/CD Strategy

The `ci/pipeline.yml` referenced in Section 3.2 is intentionally
two-speed: a fast, narrow check on every pull request, and a full
cross-browser/mobile regression on a schedule. Running the entire
BrowserStack matrix on every PR would be both slow and expensive; running
nothing beyond unit tests until a nightly job would let UI/API
regressions sit for up to a day.

```text
Pull Request
    |
    v
Lint + API smoke tests  (fast, no browsers)
    |
    v
Playwright smoke tests  (Chromium only, critical paths, isolated test data)
    |
    v
Upload traces / screenshots / console+network logs on any failure
    |
    v
Merge gate: PR blocked only on the above — not on the full matrix

Nightly (scheduled)
    |
    v
Full regression: Chrome + Firefox + BrowserStack real Safari
    |
    v
Mobile matrix via BrowserStack (real devices)
    |
    v
Full test-data cleanup sweep + results to reporting dashboard
```

**PR pipeline runs:**
- API smoke tests.
- Critical-path UI tests, Chromium only.
- Isolated, uniquely-named test data per run (Section 3.5).

**Nightly pipeline adds:**
- Chrome, Firefox, and BrowserStack real Safari sessions.
- The full mobile device matrix via BrowserStack.
- Full regression suite, not just critical paths.

**On any failure, regardless of pipeline:**
- Playwright trace file.
- Screenshot and video (BrowserStack sessions record these automatically).
- Console and network logs.
- API request/response logs from the failing step.

## 6. Assumptions & Implementation Notes

See [`docs/testing-approach.md`](testing-approach.md) for the full list —
it covers the specific assumptions behind Parts 1 and 3 (seeded test
accounts, `data-testid` availability, 2FA handling, native-vs-responsive
mobile scope, API token strategy, environment topology, cleanup, and the
direct-URL tenant-isolation check), plus the framework-level open
questions from Section 3.6.

## 7. Final Testing Philosophy

Good test automation for a multi-tenant B2B platform isn't about
maximizing coverage per test — it's about making failures cheap to
diagnose, keeping tenant boundaries provably enforced at every layer they
could leak from (API, UI list, and direct navigation, not just one), and
building a framework that survives the platform adding new roles,
tenants, and platforms without a rewrite. The specific tools here —
Playwright, pytest, BrowserStack — matter less than that underlying
discipline, which is why the framework in Section 3 is built to let the
tooling underneath change without the tests themselves changing.
