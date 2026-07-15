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

Release tags use exact `vX.Y.Z`; Docker image tags drop the `v` prefix. Each segment is one digit: `v1.0.9` rolls to `v1.1.0`, `v1.1.9` to `v1.2.0`, and `v1.9.9` to `v2.0.0`. Published `v1.0.10` through `v1.0.13` remain immutable history.

HolyCode ships many third-party CLIs inside one Docker image. Tagged releases refresh the pinned Dockerfile tools, but optional OpenCode plugins are live registry installs trusted at container startup when you enable them. Those boot-installed plugins are outside the image SBOM. Renovate configuration covers images, Actions, npm, PyPI, GitHub releases, and plugin pins; release audits still record scanner findings and compatibility holds before publication.

Trivy's release gate keeps its full critical/high report visible and blocks fixable critical findings. The dated versions, holds, removals, and scanner disposition are recorded in [`docs/dependency-audit-v1.1.1.md`](../docs/dependency-audit-v1.1.1.md).

When `ENABLE_PAPERCLIP=true`, HolyCode exposes an authenticated local agent board on the configured Paperclip port. Keep that port on trusted LAN/private networks or behind a VPN, and do not publish it directly to the public internet.

When `ENABLE_HERMES=true`, set `API_SERVER_KEY` and keep port `8642` on a trusted network. If you enable CLIProxyAPI integration, keep the external endpoint private and protect its config, auth files, and API key outside HolyCode.

Netlify CLI is installed without its platform-specific local functions binaries. HolyCode supports remote build/deploy commands only; `netlify dev` and local functions are intentionally unsupported until upstream rebuilds those binaries.
