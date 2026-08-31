# Testing Approach — Assumptions & Implementation Notes

## Reliability strategy (Part 1)

The rule behind every fix in `tests/part1/test_login.py`: wait for
application state, not for time or network activity. Every wait is tied to
something the app itself exposes — a locator becoming visible, a URL
actually changing, an account's declared auth shape — rather than a fixed
sleep, a `networkidle` heuristic, or an inferred 2FA timeout. Combined with
per-test browser-context isolation (via `pytest-playwright`) and
CI-secret-backed credentials, this removes the shared-state and timing
assumptions that caused the original flakiness, and it degrades
gracefully: a genuinely slow tenant gets more time via the same locator
wait, instead of needing a different code path.

## Implementation notes

- **Playwright vs. Selenium (Part 3 mobile test).** `tests/mobile/` and
  the mobile method in `tests/integration/test_project_creation_flow.py`
  use Selenium against BrowserStack's hub, while every web test uses
  Playwright. This is deliberate: BrowserStack's real-device mobile
  support is most mature via Selenium/Appium, while Playwright's own
  BrowserStack integration is newer and may not cover every device/OS
  combination a team needs. A fuller framework would put a
  `DriverFactory` in front of both so test authors ask for "iPhone 14 /
  Safari" and get a driver back, without knowing which library is
  underneath (see `docs/case-study-solution.md`, Section 3.3).
- **Split integration tests, not one monolithic flow.** The case study
  frames Part 3 as a single `test_project_creation_flow()`. It's
  implemented here as three independent tests
  (`test_project_creation_flow`, `test_mobile_accessibility`,
  `test_tenant_isolation`) sharing the same `created_project` fixture, so
  a mobile-specific failure (e.g. a BrowserStack device unavailable)
  doesn't prevent the API/UI and tenant-isolation checks from running and
  reporting their own result.
- **WebKit is not Safari.** Playwright's WebKit engine gives fast local
  signal but is not the same build as Apple's Safari. Actual Safari
  coverage runs through BrowserStack's real Safari sessions
  (`config/browserstack.example.yaml`), not local WebKit.

## Assumptions

- Test accounts are pre-seeded in a dedicated QA/staging tenant per
  company, with credentials injected via CI secrets, and each account's
  `requires_2fa` setting is known ahead of time rather than detected at
  runtime.
- Key elements (project cards, dashboard containers, list containers)
  expose stable `data-testid` attributes. If they don't today, adding
  them is a recommendation worth raising on its own — test hooks are
  more stable across redesigns than CSS classes or copy.
- 2FA for automated test accounts uses a fixed/seeded OTP the runner can
  read from an env var for accounts where `requires_2fa` is true.
- "Mobile" is treated as the responsive web app in a real-device mobile
  browser via BrowserStack Automate. A separate native app would need
  BrowserStack App Automate + Appium against an uploaded build instead.
- API authentication uses a static per-tenant bearer token for test
  accounts; a real implementation might instead need a login/
  token-exchange call first.
- The environment under test is a shared staging environment reachable
  by both the CI runner and BrowserStack's cloud.
- A nightly cleanup sweep exists (or would be added) to catch test data
  orphaned by a crashed run, since the per-test teardown alone doesn't
  cover that case.
- Direct-URL tenant isolation assumes the app returns an HTTP-level
  403/404 for a cross-tenant project URL; if it instead renders a 200
  with an in-page "access denied" state, the check would assert on that
  locator instead of the response status.

## Open questions I'd ask the team

See `docs/case-study-solution.md`, Section 3.6, for the full list (test
data lifecycle, reporting tooling, BrowserStack session budget,
flaky-test policy, environment topology, native vs. responsive mobile
scope, 2FA bypass strategy, browser/version support matrix, data
privacy, CI trigger strategy, ownership, and non-functional testing
scope).

## Final testing philosophy

Good test automation for a multi-tenant B2B platform isn't about
maximizing coverage per test — it's about making failures cheap to
diagnose, keeping tenant boundaries provably enforced at every layer they
could leak from (API, UI list, and direct navigation, not just one), and
building a framework that survives the platform adding new roles,
tenants, and platforms without a rewrite. The specific tools — Playwright,
pytest, BrowserStack — matter less than that underlying discipline.
