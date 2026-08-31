# Bynry QA Automation Case Study

## Overview

This repository contains my solution for the Bynry (WorkFlow Pro) QA
Automation Engineering Intern case study. It covers flaky-test debugging,
a multi-platform test automation framework design, and an API + UI +
mobile integration test for a multi-tenant B2B SaaS platform.

The full written solution — including reasoning for every decision — is in
[`docs/case-study-solution.md`](docs/case-study-solution.md). This README
covers how to set up and run the code in `tests/`.

## Technologies

- Python, pytest
- Playwright (web UI)
- Selenium + BrowserStack (mobile / cross-browser)
- `requests` (API testing)
- GitHub Actions–style CI/CD concepts (see `docs/case-study-solution.md`, Section 5)

## Case study areas

### Part 1 — Flaky test debugging (`tests/part1/`)
- Identified 11 causes of flaky Playwright tests (dynamic loading,
  unhandled 2FA, one-shot assertions, shared test accounts, and more)
- Replaced timing assumptions (`networkidle`, `is_visible()` snapshots)
  with state-based waits (`expect()`, `wait_for_url()`)
- Deterministic per-account 2FA handling instead of timeout-based detection
- Isolated browser context per test, externalized credentials

### Part 2 — Framework design (`docs/case-study-solution.md`, Section 3)
- Page Object Model + API client abstraction
- Test data factories with per-run unique naming
- Multi-tenant / multi-environment configuration layering
- Browser/device configuration via a single `config/browserstack.example.yaml`
- CI/CD strategy: fast PR pipeline vs. full nightly regression

### Part 3 — API + UI + mobile integration (`tests/api/`, `tests/web/`, `tests/mobile/`, `tests/integration/`)
- API-created project as source of truth, verified through web UI and
  BrowserStack mobile as read-only observers
- Tenant isolation checked at three layers: API response code, UI list
  visibility, and direct URL navigation

## Project structure

```text
bynry-qa-automation-case-study/
├── README.md
├── docs/
│   ├── case-study-solution.md   # full write-up: all 3 parts, reasoning, code walkthroughs
│   ├── test-plan.md             # scope, test types, priority (P0/P1/P2)
│   └── testing-approach.md      # assumptions, implementation notes, testing philosophy
├── conftest.py                  # shared fixtures: API client, tenant/test-account config, test data
├── tests/
│   ├── part1/test_login.py
│   ├── api/test_projects_api.py
│   ├── web/test_project_ui.py
│   ├── mobile/test_mobile_project.py
│   └── integration/test_project_creation_flow.py
├── data/
│   ├── test_users.example.json
│   └── test_projects.example.json
├── config/
│   └── browserstack.example.yaml
├── reports/README.md
├── requirements.txt
├── pytest.ini
├── .gitignore
└── .env.example
```

## Setup

```bash
git clone <repository-url>
cd bynry-qa-automation-case-study
python -m venv .venv

# macOS / Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -r requirements.txt
playwright install
```

## Environment variables

Copy `.env.example` to `.env` and fill in test credentials, API tokens,
and BrowserStack keys:

```bash
cp .env.example .env
```

`.env` is git-ignored. Never commit real credentials —
`data/test_users.example.json` and `.env.example` show the expected
*shape* of this data only.

## Running tests

```bash
pytest                              # everything
pytest tests/part1                  # flaky-test fixes only
pytest tests/api                    # API layer only
pytest -m "not mobile"              # skip BrowserStack mobile tests (no BrowserStack account needed)
```

## Reporting

See [`reports/README.md`](reports/README.md) — this repo does not include
fabricated pass/fail screenshots, since `app.workflowpro.com` is an
illustrative endpoint from the case study prompt rather than a live,
provisioned environment. Running `pytest --html=reports/report.html`
(or enabling Playwright's trace/video options) against a real configured
environment produces genuine reports, traces, and screenshots in
`reports/`.

## Assumptions

See [`docs/testing-approach.md`](docs/testing-approach.md).
