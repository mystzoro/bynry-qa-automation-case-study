# Reports

The case study environment uses illustrative WorkFlow Pro endpoints and
credentials that were not provided as an executable test environment.
Therefore, no fabricated execution results (screenshots, "100% passed"
summaries, etc.) are included in this repository.

The framework is structured to generate real reports, screenshots, traces,
and logs when run against a configured QA environment:

```bash
# Playwright HTML report
pytest --html=reports/report.html --self-contained-html

# Playwright trace on first retry (add to pytest.ini addopts, or pass via CLI)
pytest --tracing=retain-on-failure

# BrowserStack sessions record video/screenshots automatically per session
# and are viewable from the BrowserStack Automate/App Automate dashboard.
```

Generated reports are git-ignored (`reports/generated/`, per `.gitignore`)
so this directory stays clean in version control while still being the
designated output location in CI.
