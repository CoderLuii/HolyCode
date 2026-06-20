# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in HolyCode:

1. **Do not** open a public GitHub issue
2. Email **CoderLuii@outlook.com** with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
3. You will receive a response within 48 hours

## Supported Versions

| Version | Supported |
|---------|-----------|
| latest Docker image | Yes |
| current GitHub release | Yes |
| < 1.0.0 | No        |

HolyCode ships many third-party CLIs inside one Docker image. Tagged releases refresh the pinned Dockerfile tools, but optional OpenCode plugins are installed by OpenCode at container startup when you enable them. Dependabot alerts are not currently enabled for this repository, so release audits record npm, PyPI, OSV, Docker, and workflow checks directly.

When `ENABLE_PAPERCLIP=true`, HolyCode exposes an authenticated local agent board on the configured Paperclip port. Keep that port on trusted LAN/private networks or behind a VPN, and do not publish it directly to the public internet.
