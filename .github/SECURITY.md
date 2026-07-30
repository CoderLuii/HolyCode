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

HolyCode ships many third-party CLIs inside one Docker image. Tagged releases refresh the pinned Dockerfile tools. The supported Claude Auth plugin is packaged inside the image and installed from that offline payload when enabled. Plugins you install yourself remain outside the image SBOM. Renovate configuration covers images, Actions, npm, PyPI, GitHub releases, and plugin pins; release audits still record scanner findings and compatibility holds before publication.

Trivy's release gate keeps its full critical/high report visible and blocks every unexcepted fixable critical or high finding. Docker Scout applies the same gate. Narrow exceptions must name one CVE and package, match the installed and approved-source versions, explain reachability and controls, expire within 30 days, and name an exact removal trigger. npm lifecycle scripts are disabled during installation, then checked against exact package versions, integrity values, script bodies, and architecture rules before approved scripts run. The dated versions, holds, removals, exceptions, and scanner disposition are recorded in [`docs/dependency-audit-v1.1.4.md`](../docs/dependency-audit-v1.1.4.md).

When `ENABLE_PAPERCLIP=true`, HolyCode exposes an authenticated local agent board on the configured Paperclip port. Keep that port on trusted LAN/private networks or behind a VPN, and do not publish it directly to the public internet.

Bundled Hermes remains unavailable in v1.1.4 because its current releases require vulnerable dependency pins. HolyCode preserves `/home/opencode/.hermes`, and `ENABLE_HERMES=true` stops startup with a migration message. HolyCode-managed oh-my-openagent installation is also suspended; `ENABLE_OH_MY_OPENAGENT=true` stops startup without changing existing configuration. If you manage that plugin yourself, you accept its current upstream dependency risk. If you enable CLIProxyAPI integration, keep the external endpoint private and protect its config, auth files, and API key outside HolyCode.

Chromium 150.0.7871.181 runs as the `opencode` user with its setuid sandbox enabled. Debian Trixie had not published 150.0.7871.186 on 07/30/2026, so `CVE-2026-16804` through `CVE-2026-16807` are tracked in `config/security-exceptions-v1.1.4.json` through 08/28/2026. Keep `config/chromium-seccomp.json` attached through Compose or the equivalent Podman `--security-opt` option. Do not work around browser failures with `--no-sandbox`, `SYS_ADMIN`, or `seccomp=unconfined`.

Netlify CLI and `serve` are not bundled in v1.1.4.
