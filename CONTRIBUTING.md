# Contributing to QA Automation Case Study

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

This project is open and welcoming to all contributors. We're committed to providing a positive and productive environment for collaboration.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/bynry-qa-automation-case-study.git
   cd bynry-qa-automation-case-study
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or: .venv\Scripts\activate on Windows

# Install dependencies and development tools
pip install -r requirements.txt
pip install ruff pytest-cov

# Install Playwright browsers
playwright install
```

## Making Changes

### Code Style

- **Python**: Follow [PEP 8](https://pep8.org/)
- **Imports**: Group and sort imports (stdlib → third-party → local)
- **Naming**: Use descriptive names for functions, variables, and test cases
- **Documentation**: Add docstrings to functions and classes
- **Type Hints**: Use type hints for improved code clarity

### Linting and Formatting

Before committing, run linting:
```bash
ruff check .
```

To fix common issues automatically:
```bash
ruff check . --fix
```

### Testing

Ensure all tests pass:
```bash
pytest
```

For test coverage:
```bash
pytest --cov=. --cov-report=html
```

### Writing Tests

When adding new functionality:
1. Write tests first (TDD approach is preferred)
2. Tests should be in the appropriate `tests/` subdirectory
3. Use descriptive test names: `test_<feature>_<scenario>`
4. Include docstrings explaining test purpose
5. Use fixtures from `conftest.py` for common setup

Example:
```python
def test_api_creates_project_with_valid_credentials(api_client, test_user):
    """Verify API creates project successfully with valid user credentials."""
    response = api_client.create_project(
        name="Test Project",
        tenant_id=test_user["tenant_id"]
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Project"
```

## Commit Guidelines

1. **Atomic commits**: Each commit should represent a single logical change
2. **Clear messages**: Use descriptive commit messages
   - Good: `Add tenant isolation test for web UI layer`
   - Poor: `fix bug` or `update code`
3. **Reference issues**: If fixing an issue, reference it: `Closes #123`

Example commit message:
```
Add comprehensive tenant isolation verification

- Verify API response codes for cross-tenant access
- Check UI list visibility for tenant data
- Test direct URL navigation restrictions
- Closes #45
```

## Pull Request Process

1. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open a Pull Request** on GitHub with:
   - Clear title describing the change
   - Description of what changed and why
   - Reference to any related issues
   - Screenshot/log output if applicable

3. **PR checklist**:
   - [ ] All tests pass (`pytest`)
   - [ ] Code follows style guidelines (`ruff check .`)
   - [ ] New tests added for new functionality
   - [ ] Documentation updated if needed
   - [ ] Commit messages are clear and atomic
   - [ ] No hardcoded credentials or secrets

4. **Review process**:
   - Address any feedback from reviewers
   - Push additional commits to the same branch
   - PR will be merged once approved

## Areas for Contribution

### Enhancements
- Additional test cases for edge cases
- Improved error messages and logging
- Performance optimizations
- New testing patterns or examples

### Documentation
- Clarify existing documentation
- Add examples and use cases
- Write tutorials or guides
- Improve comments in code

### Bug Fixes
- Report issues with clear reproduction steps
- Submit PRs with fixes and tests
- Help triage and validate reported issues

## Questions or Need Help?

- Open an issue for bug reports or feature requests
- Use clear, descriptive titles and descriptions
- Include steps to reproduce for bugs
- Link related issues or PRs

## License

By contributing to this project, you agree that your contributions will be licensed under its MIT License.

---

**Thank you for contributing!** 🎉
