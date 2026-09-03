# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability, please email:

**rajatgupta116@gmail.com**

Include:
1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if any)

You should receive a response within 48 hours.

## Security Considerations

### API Keys and Credentials

- **Never commit** API keys, credentials, or tokens
- Use `.env` files (gitignored) for local development
- Use environment variables or secrets management in production
- Rotate keys if accidentally committed

### Data Privacy

FireTwin processes:
- ✅ **Public satellite data** (NASA FIRMS, NIFC)
- ✅ **Public weather reanalysis** (ERA5-Land)
- ✅ **Public land cover data** (LANDFIRE, USGS)

No personally identifiable information (PII) is collected or stored.

### Input Validation

All API inputs are validated with Pydantic schemas to prevent:
- Injection attacks
- Path traversal
- Arbitrary file access
- Resource exhaustion

### Dependencies

- Conda environment pins major versions
- Regular updates for security patches
- GitHub Dependabot enabled for alerts
- CI runs security scans

### Safe Defaults

- API rate limiting enabled
- Maximum file size limits enforced
- Sandboxed computation (when implemented)
- No arbitrary code execution from user input

## Known Limitations

### Research Prototype Status

FireTwin is a **research prototype** and should not be used for:
- Operational wildfire response
- Evacuation planning
- Safety-critical decisions
- Production systems without thorough security review

### Data Source Trust

FireTwin relies on external data sources:
- NASA FIRMS
- NIFC/WFIGS
- Copernicus CDS
- USGS/LANDFIRE

We trust these authoritative sources but:
- Validate data formats and ranges
- Handle network errors gracefully
- Cache responses to reduce attack surface
- Document data provenance

## Security Best Practices

### For Users

1. **Protect your API keys**:
   - Store in `.env` files
   - Don't share or commit them
   - Rotate if compromised

2. **Keep software updated**:
   ```bash
   conda env update -f environment.yml
   pip install --upgrade pip
   ```

3. **Review code before running**:
   - Especially notebooks and scripts
   - Check for suspicious network calls

### For Developers

1. **Dependency Security**:
   ```bash
   # Check for known vulnerabilities
   pip-audit  # (if available)
   ```

2. **Secret Scanning**:
   ```bash
   # Before committing
   git secrets --scan
   ```

3. **Code Review**:
   - All PRs require review
   - Look for injection vulnerabilities
   - Validate input handling

4. **Least Privilege**:
   - Run with minimal permissions
   - Avoid root/admin privileges
   - Sandbox untrusted operations

## Disclosure Policy

When we receive a security vulnerability report:

1. **Acknowledge** within 48 hours
2. **Investigate** and confirm the issue
3. **Develop a fix** in private
4. **Test** the fix thoroughly
5. **Release** patched version
6. **Disclose** details after fix is widely deployed

We follow responsible disclosure practices.

## Security Tools

### Enabled

- ✅ Pre-commit hooks for secret detection
- ✅ GitHub Actions CI with security checks
- ✅ Dependency version pinning
- ✅ Input validation with Pydantic

### Planned

- ⬜ SAST (Static Application Security Testing)
- ⬜ Dependency scanning (Snyk, Dependabot)
- ⬜ Container scanning (when using Docker)
- ⬜ Regular penetration testing

## Contact

For security concerns: **rajatgupta116@gmail.com**

For general questions: Open a GitHub Discussion

---

**Note**: This is a research project. While we take security seriously, it has not undergone a professional security audit. Use at your own risk.
