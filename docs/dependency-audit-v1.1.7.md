# HolyCode v1.1.7 Dependency Audit

This recovery starts from Git commit `8d7c87c29d678fc8726605438444608e6b0b3c0f` with Git predecessor `v1.1.6`. The published image predecessor remains `coderluii/holycode:1.1.5@sha256:804ec668b97466dba9a26ded8af258fabc2d778047b7c8aebdaab7bccd9a3ae8` because the v1.1.6 release workflow did not promote its candidate to the public image aliases.

## Accepted fixes

| Component | Version | Release control |
|---|---:|---|
| npm nested `ip-address` | 10.3.1 | npm registry integrity `sha512-1e9d3kb97NHJTIJDZW9rKqW2h6+dFa50Dy0fpPSMQp2ADje5gvKsXmdiK6dwY5t76TaTt5+P5N1Y/LoToIxP6g==`; compatible `socks` declaration, installed tree, and npm runtime validated |
| PM2 nested `js-yaml` | 4.3.1 | npm registry integrity `sha512-CY6crGq313MX8GkwvB7tzgp99vjQxY1++5y10/BKN/GUfHqWaOGQMNZkBvqSzsZKWk/ijwHlWzzkLulsGHhjWQ==`; PM2 declaration, installed tree, and runtime validated |

The rest of the v1.1.6 dependency set is unchanged. The v1.1.7 image rebuild still refreshes Debian packages from the configured Trixie repositories.

## Pre-tag architecture and scanner gates

Manual validation on `main` builds and smoke-tests native `linux/amd64` and `linux/arm64` images. Each architecture then runs Docker Scout 1.24.0 and Trivy 0.73.0 with fixable critical and high findings fail-closed. The workflow uploads the exact commit SHA, image ID, package inventory, SPDX SBOM, and full and fixable scanner reports as architecture-specific evidence.

The tagged-release workflow remains authoritative for the candidate digest that is eventually published. Scanner databases can change after this audit, so each release run evaluates the exact candidate again before promotion.
