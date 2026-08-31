# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, **please do not open a public issue**. Instead:

1. **Email** the vulnerability details to the repository owner
2. **Include**: 
   - Description of the vulnerability
   - Steps to reproduce (if applicable)
   - Potential impact
   - Suggested fix (if available)

3. **Timeline**:
   - We will acknowledge receipt within 48 hours
   - We will work on a fix and provide an update within 7 days
   - We will release a patch version and credit you (if desired)

## Security Best Practices

When using this project:

- **Never commit credentials** to version control
- **Always use `.env.example`** as a template and keep `.env` in `.gitignore`
- **Rotate credentials regularly**, especially if exposed
- **Use strong passwords** for all test accounts
- **Store secrets in CI/CD secret managers**, not in code or logs
- **Review logs and reports** carefully before sharing (remove sensitive data)

## Dependencies

This project regularly updates its dependencies to address known vulnerabilities:

```bash
pip install --upgrade -r requirements.txt
```

For dependency vulnerability scanning:
```bash
pip install safety
safety check
```

---

**Thank you for helping keep this project secure!**
