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

HolyCode ships many third-party CLIs inside one Docker image. Tagged releases refresh the pinned Dockerfile tools. The supported Claude Auth plugin is packaged inside the image and installed from that offline payload when enabled. Plugins you install yourself remain outside the image SBOM. Renovate configuration covers images, Actions, npm, PyPI, GitHub releases, and plugin pins; release audits still record scanner findings and compatibility holds before publication.

Trivy and Docker Scout keep their full critical/high reports visible and block every fixable critical or high finding. A passing fixable gate does not mean the image has zero vulnerabilities: findings without an available fix remain visible in the release evidence. npm lifecycle scripts are disabled during installation, then checked against exact package versions, integrity values, script bodies, and architecture rules before approved scripts run. Current decisions and owner-guarded replacements are recorded in [`docs/dependency-audit-v1.1.9.md`](../docs/dependency-audit-v1.1.9.md); historical decisions remain in their dated audits.

When `ENABLE_PAPERCLIP=true`, HolyCode exposes an authenticated local agent board on the configured Paperclip port. Keep that port on trusted LAN/private networks or behind a VPN, and do not publish it directly to the public internet.

The bundled Hermes service is currently unavailable. HolyCode preserves `/home/opencode/.hermes`, and `ENABLE_HERMES=true` stops startup with a migration message. HolyCode-managed oh-my-openagent installation is also suspended; `ENABLE_OH_MY_OPENAGENT=true` stops startup without changing existing configuration. A manually installed plugin is user-managed and outside the image's release validation. If you enable CLIProxyAPI integration, keep the external endpoint private and protect its config, auth files, and API key outside HolyCode.

Chromium comes from Debian Trixie security packages and runs as the `opencode` user with its setuid sandbox enabled. Keep the image current, keep `config/chromium-seccomp.json` attached through Compose or the equivalent Podman `--security-opt` option, and review the release SBOM/scanner assets for the exact shipped package inventory. Do not work around browser failures with `--no-sandbox`, `SYS_ADMIN`, or `seccomp=unconfined`.

Netlify CLI and `serve` are not bundled. The consolidated notice is available inside the container at `/usr/local/share/holycode/THIRD-PARTY-NOTICES`.
