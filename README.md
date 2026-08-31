# QA Automation Case Study — WorkFlow Pro

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![pytest](https://img.shields.io/badge/pytest-8.0+-green.svg)](https://pytest.org/)
[![Playwright](https://img.shields.io/badge/Playwright-1.44+-brightgreen.svg)](https://playwright.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> A comprehensive QA automation case study covering **flaky test debugging**, **multi-platform framework design**, and **end-to-end integration testing** for a multi-tenant B2B SaaS platform.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Key Highlights](#key-highlights)
- [Project Structure](#project-structure)
- [Technologies](#technologies)
- [Setup Instructions](#setup-instructions)
- [Running Tests](#running-tests)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This repository demonstrates **professional-grade QA automation practices** through three interconnected case studies:

1. **Part 1 — Flaky Test Debugging** (`tests/part1/`)
   - Root-cause analysis of 11 common test flakiness patterns
   - Solutions using Playwright's auto-retrying assertions and state-based waits
   - Deterministic credential and 2FA handling
   - Complete browser context isolation

2. **Part 2 — Framework Design** (see `docs/case-study-solution.md`, Section 3)
   - Scalable Page Object Model with API client abstraction
   - Test data factories with unique naming per run
   - Multi-tenant and multi-environment configuration
   - CI/CD-ready test categorization

3. **Part 3 — Integration Testing** (`tests/api/`, `tests/web/`, `tests/mobile/`, `tests/integration/`)
   - API-first testing approach with UI verification layer
   - Cross-platform validation (web, mobile, BrowserStack)
   - Tenant isolation verification at three independent layers

**Full reasoning and code walkthroughs**: [`docs/case-study-solution.md`](docs/case-study-solution.md)

---

## Quick Start

```bash
# Clone and enter directory
git clone https://github.com/mystzoro/bynry-qa-automation-case-study.git
cd bynry-qa-automation-case-study

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # or: .venv\Scripts\activate on Windows

# Install dependencies and browsers
pip install -r requirements.txt
playwright install

# Configure environment
cp .env.example .env
# Edit .env with your test credentials and API keys

# Run all tests
pytest

# View test collection
pytest --collect-only
```

## Key Highlights

| Focus | Solution | Benefit |
|-------|----------|---------|
| **Flaky Tests** | Auto-retrying `expect()` assertions + explicit waits | Deterministic test execution across all environments |
| **Test Isolation** | Per-test browser contexts + unique test data | Safe parallel execution and CI/CD scalability |
| **Configuration** | YAML-based browser/tenant/role matrix | Single source of truth for all test parameters |
| **Credentials** | Externalized via `.env` + per-account 2FA flags | Secure, auditable, maintainable test setup |
| **Multi-tenant** | Three-layer isolation verification | Comprehensive data privacy validation |
| **CI/CD Ready** | Fast PR pipeline vs. nightly regression strategy | Clear testing philosophy for different deployment gates |

## Technologies

- **Language & Framework**: Python 3.8+, pytest 8.0+
- **Web Automation**: Playwright 1.44+ (Chromium, Firefox, WebKit)
- **Mobile Testing**: Selenium 4.20+ with BrowserStack
- **API Testing**: requests 2.31+
- **Configuration**: PyYAML 6.0+, python-dotenv 1.0+
- **Resilience**: pytest-rerunfailures 14.0+

## Project Structure

```
bynry-qa-automation-case-study/
├── README.md                                    # This file
├── docs/
│   ├── case-study-solution.md                   # Full write-up: all 3 parts, reasoning, walkthroughs
│   ├── test-plan.md                             # Scope, test types, priorities (P0/P1/P2)
│   └── testing-approach.md                      # Implementation philosophy & assumptions
├── conftest.py                                  # Shared pytest fixtures: API client, auth, test data
├── pytest.ini                                   # pytest configuration
├── requirements.txt                             # Python dependencies
├── tests/
│   ├── part1/test_login.py                      # Flaky test fixes with state-based waits
│   ├── api/test_projects_api.py                 # REST API layer validation
│   ├── web/test_project_ui.py                   # Web UI verification
│   ├── mobile/test_mobile_project.py            # Mobile / cross-browser via BrowserStack
│   └── integration/test_project_creation_flow.py # End-to-end: API → Web → Mobile
├── data/
│   ├── test_users.example.json                  # Template for test account structure
│   └── test_projects.example.json               # Template for test project data
├── config/
│   └── browserstack.example.yaml                # Browser/device configuration matrix
├── reports/
│   └── README.md                                # Test reporting guidelines
└── .env.example                                 # Template for environment variables (credentials, API keys)
```

---

## Setup Instructions

### Prerequisites

- **Python 3.8** or higher
- **pip** (included with Python)
- **Git**

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mystzoro/bynry-qa-automation-case-study.git
   cd bynry-qa-automation-case-study
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment:**
   
   **macOS / Linux:**
   ```bash
   source .venv/bin/activate
   ```
   
   **Windows:**
   ```bash
   .venv\Scripts\activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Install Playwright browsers:**
   ```bash
   playwright install
   ```

6. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your credentials:
   - Test user accounts (username/password for different tenant roles)
   - API base URL and authentication tokens
   - BrowserStack credentials (if testing mobile/cross-browser)
   - Any 2FA configuration per account

### Environment Variables Reference

```env
# API Configuration
API_BASE_URL=https://api.workflowpro.com
API_TOKEN=your_api_token_here

# Test Credentials (different tenants/roles)
COMPANY1_ADMIN_EMAIL=admin@company1.com
COMPANY1_ADMIN_PASSWORD=your_password
COMPANY1_REQUIRES_2FA=true
COMPANY1_2FA_METHOD=authenticator  # or: sms, email

COMPANY2_ADMIN_EMAIL=admin@company2.com
COMPANY2_ADMIN_PASSWORD=your_password
COMPANY2_REQUIRES_2FA=false

# BrowserStack (Optional - for mobile/cross-browser tests)
BROWSERSTACK_USERNAME=your_username
BROWSERSTACK_ACCESS_KEY=your_key
```

> **⚠️ Security Note**: Never commit `.env` to version control. The `.gitignore` file already excludes it. Always use `.env.example` as the template.

---

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Suites

```bash
# Part 1: Flaky test debugging fixes
pytest tests/part1 -v

# API layer only
pytest tests/api -v

# Web UI tests
pytest tests/web -v

# Integration tests (API → Web → Mobile)
pytest tests/integration -v

# Exclude mobile tests (if BrowserStack not configured)
pytest -m "not mobile"
```

### Advanced Options

```bash
# Collect tests without running
pytest --collect-only

# Run with detailed output
pytest -v -s

# Run with 3 retries for flaky tests
pytest --reruns 3

# Run in parallel (requires pytest-xdist)
pytest -n auto

# Generate HTML report
pytest --html=reports/report.html --self-contained-html

# Show slowest tests
pytest --durations=10

# Stop after first failure
pytest -x

# Run only tests matching a pattern
pytest -k "login" -v
```

### Test Markers

Tests can be filtered by marker:

```bash
pytest -m "not mobile"           # Skip mobile tests
pytest -m "api"                  # Only API tests
pytest -m "integration"          # Only integration tests
```

---

## Documentation

### Main Case Study Write-Up
**[`docs/case-study-solution.md`](docs/case-study-solution.md)** — Complete reasoning behind every decision:
- **Section 1**: Executive summary of approach
- **Section 2**: Deep dive into all 11 flaky test issues and fixes
- **Section 3**: Framework architecture and design patterns
- **Section 4**: Integration test implementation details
- **Section 5**: CI/CD strategy and test categorization

### Additional Documentation
- **[`docs/test-plan.md`](docs/test-plan.md)** — Scope, test types, and priority levels
- **[`docs/testing-approach.md`](docs/testing-approach.md)** — Assumptions and implementation notes
- **[`reports/README.md`](reports/README.md)** — Test reporting setup

---

## Case Study Details

### Part 1 — Flaky Test Debugging

**Problem:** Tests pass locally but fail intermittently in CI.

**11 Root Causes Identified:**
1. No wait for app to hydrate before interaction
2. No wait for async operations to complete
3. Race conditions on SPA client-side routing
4. One-time boolean snapshots instead of polling
5. Unhandled 2FA for some accounts
6. Hardcoded credentials in source
7. No test isolation between parallel workers
8. Browser/context not cleaned up on failure
9. Dynamic element lists captured at wrong time
10. No viewport/browser/timeout configuration
11. No diagnostics (screenshot/trace/logs) on failure

**Solutions Implemented:**
- ✅ Playwright `expect()` with auto-retry assertions
- ✅ `wait_for_url()` and application-state waits
- ✅ Per-account 2FA handling with explicit branching
- ✅ Externalized credentials via `.env`
- ✅ Isolated browser context per test
- ✅ Fixture-based teardown with guaranteed cleanup
- ✅ Fixture-scoped test data with unique naming
- ✅ Configurable viewport and browser via `conftest.py`
- ✅ Screenshot/trace capture on failure

**See:** [`tests/part1/test_login.py`](tests/part1/test_login.py)

### Part 2 — Framework Design

**Architecture:**
- **Page Objects**: Abstraction layer for UI element interaction
- **API Client**: Typed requests wrapper with auth and error handling
- **Fixtures**: Test data factories, tenant config, browser/device setup
- **Configuration**: Multi-level YAML-based tenant/environment/browser matrix

**Scalability:**
- Independent test data per run (no shared state)
- Tenant × Role × Environment × Browser combinations without code duplication
- Fast unit-like tests (API only) vs. full E2E (all layers)

**See:** [`docs/case-study-solution.md`, Section 3](docs/case-study-solution.md#section-3)

### Part 3 — Integration Testing

**Approach:**
1. **API Layer** (Source of Truth)
   - Create test data via API
   - Verify response codes and payloads
   - Test tenant isolation at API boundary

2. **Web UI Layer** (Read-Only Observer)
   - Navigate to app and log in
   - Verify API-created data appears in UI
   - Check tenant isolation in UI list

3. **Mobile Layer** (Read-Only Observer)
   - Run same flow on BrowserStack mobile device
   - Verify API data is accessible on mobile
   - Ensure no cross-tenant data leakage

**See:** [`tests/integration/test_project_creation_flow.py`](tests/integration/test_project_creation_flow.py)

---

## Contributing

Contributions are welcome! Here's how:

1. **Fork** this repository
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make your changes** and ensure all tests pass: `pytest`
4. **Commit with clear messages**: `git commit -m "Add your message"`
5. **Push to your fork**: `git push origin feature/your-feature`
6. **Open a Pull Request** with a description of your changes

### Code Style

- **Formatting**: Follow [PEP 8](https://pep8.org/)
- **Linting**: Run `ruff check .` to check for issues
- **Type Hints**: Use type hints where practical
- **Tests**: All new features must include tests

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
