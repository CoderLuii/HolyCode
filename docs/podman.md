# HolyCode with Podman

Podman can run the same HolyCode image as Docker. Use this guide when you prefer a daemonless or rootless container runtime, especially on Fedora, RHEL, CoreOS, Rocky, AlmaLinux, or similar Linux hosts.

This guide mirrors the minimal HolyCode web UI setup. For the full Docker Compose profile and sidecar services, use the main README and `docker-compose.full.yaml`.

## What this guide covers

- Running the HolyCode web UI with `podman run`
- Keeping OpenCode state, cache, and workspace files in bind mounts
- Loading provider keys from `.env` with `--env-file .env`
- SELinux labels for Fedora/RHEL/CoreOS hosts
- Rootless Podman permission and user namespace notes
- Optional service boundaries for Paperclip, Hermes, and CLIProxyAPI
- Safe update and recreate behavior

## Prerequisites

Install Podman on the host and run the command from the HolyCode project folder, or from another folder that contains the same `.env.example`, data, cache, and workspace paths.

Copy the environment template and add at least one provider key:

```bash
cp .env.example .env
```

Edit `.env` and set the provider you plan to use, for example `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, or another supported provider variable.

Podman treats relative bind mount sources as paths relative to the directory where you run `podman`. Missing bind mount sources fail, so create them first.

## Minimal web UI setup

Create the host directories:

```bash
mkdir -p ./data/opencode ./local-cache/opencode ./workspace
```

Run HolyCode:

```bash
podman run -d \
  --name holycode \
  --restart unless-stopped \
  --shm-size=2g \
  -p 4096:4096 \
  -v ./data/opencode:/home/opencode \
  -v ./local-cache/opencode:/home/opencode/.cache/opencode \
  -v ./workspace:/workspace \
  --env-file .env \
  -e PUID=$(id -u) \
  -e PGID=$(id -g) \
  docker.io/coderluii/holycode:latest
```

Open http://localhost:4096.

What the important options do:

- `--shm-size=2g` gives Chromium and browser automation enough shared memory.
- `-p 4096:4096` publishes the OpenCode web UI.
- `./data/opencode:/home/opencode` persists OpenCode config, sessions, plugins, and service state.
- `./local-cache/opencode:/home/opencode/.cache/opencode` keeps plugin and package cache on local disk.
- `./workspace:/workspace` mounts your project files.
- `--env-file .env` loads provider keys and optional HolyCode toggles without putting secrets in shell history.
- `PUID` and `PGID` tell HolyCode which host UID/GID to use for file ownership inside mounted paths.
- `docker.io/coderluii/holycode:latest` fully qualifies the Docker Hub image for Podman.

If you use a different host folder, keep the container paths unchanged. `/home/opencode`, `/home/opencode/.cache/opencode`, and `/workspace` are the paths HolyCode expects inside the container.

## SELinux hosts

On SELinux hosts such as Fedora, RHEL, or CoreOS, unlabeled bind mounts can look like permission problems from inside the container. Add `:Z` to each HolyCode bind mount for a private label used by this one container:

```bash
podman run -d \
  --name holycode \
  --restart unless-stopped \
  --shm-size=2g \
  -p 4096:4096 \
  -v ./data/opencode:/home/opencode:Z \
  -v ./local-cache/opencode:/home/opencode/.cache/opencode:Z \
  -v ./workspace:/workspace:Z \
  --env-file .env \
  -e PUID=$(id -u) \
  -e PGID=$(id -g) \
  docker.io/coderluii/holycode:latest
```

Use `:z` only when the same host path must be shared by multiple containers. Do not casually relabel broad system paths or your entire home directory.

## Rootless Podman and permissions

Rootless Podman runs containers inside a user namespace. That is one of the main reasons people choose Podman, but it also means bind mount ownership can behave differently from Docker.

Check these if files are unexpectedly owned or blocked:

- Your user has ranges in `/etc/subuid` and `/etc/subgid`.
- `PUID=$(id -u)` and `PGID=$(id -g)` match the host user that should own files in `./workspace`.
- The host paths exist before running the container.
- SELinux hosts use `:Z` or `:z` labels as described above.

Some rootless setups use custom user namespace modes such as `--userns=keep-id`. Do not add that flag by default for HolyCode; it changes how the container process user is mapped. Use it only after testing that it matches your host policy and does not interfere with HolyCode's `PUID`/`PGID` remapping.

## Optional services

The command above runs the minimal HolyCode web UI on port `4096`.

Paperclip and Hermes can be enabled with the same environment variables used by the Docker Compose examples:

```env
ENABLE_PAPERCLIP=true
PAPERCLIP_PORT=3100
PAPERCLIP_DEPLOYMENT_MODE=authenticated
PAPERCLIP_BIND=lan
PAPERCLIP_ALLOWED_HOSTNAMES=192.168.1.50,my-host.local
ENABLE_HERMES=true
HERMES_PORT=8642
API_SERVER_KEY=replace-with-a-real-secret
```

If you enable them, publish the ports you need:

```bash
-p 4096:4096 \
-p 3100:3100 \
-p 8642:8642
```

Paperclip listens on `3100` when enabled. `PAPERCLIP_BIND=lan` lets the service bind inside the container so the Podman port publish can reach it. Hermes exposes an API service on `8642`; set `API_SERVER_KEY` to a real bearer token before enabling it. A `404` at `/` is normal as long as the process stays healthy.

CLIProxyAPI is different. In HolyCode it is documented as a full Compose sidecar profile, not as part of the one-container Podman command. Use `docker-compose.full.yaml` when you need the supported CLIProxyAPI sidecar workflow.

## Updating HolyCode

Pull the latest image:

```bash
podman pull docker.io/coderluii/holycode:latest
```

Then recreate the container:

```bash
podman stop holycode
podman rm holycode
```

Run the `podman run` command again. Your data stays in `./data/opencode`, `./local-cache/opencode`, and `./workspace`.

Do not use `podman start holycode` as an update path. It restarts the existing container with the old image, environment variables, ports, and mount settings.

`--restart unless-stopped` restarts the container after normal exits unless you explicitly stopped it. Reboot persistence depends on Podman's `podman-restart.service`. If you later manage HolyCode through systemd or Quadlet, use systemd's `Restart=` behavior instead of Podman's `--restart` flag.

## Troubleshooting

### Permission denied on mounted files

Verify `PUID`, `PGID`, host directory ownership, and rootless user namespace setup:

```bash
id -u
id -g
```

Make sure those values match the `PUID` and `PGID` passed to the container. If rootless Podman still maps ownership unexpectedly, check `/etc/subuid` and `/etc/subgid` for your user.

### SELinux AVC or denied access

Add `:Z` to the three bind mounts for a private container label:

```bash
-v ./data/opencode:/home/opencode:Z \
-v ./local-cache/opencode:/home/opencode/.cache/opencode:Z \
-v ./workspace:/workspace:Z
```

Use `:z` only when multiple containers must share the same host path.

### Port 4096 already in use

Publish HolyCode on a different host port while keeping the container port at `4096`:

```bash
-p 4097:4096
```

Then open http://localhost:4097.

### Chromium or browser automation fails

Make sure the command includes:

```bash
--shm-size=2g
```

Without enough `/dev/shm`, Chromium can crash or produce broken automation results.

### Environment variables did not change

Changing `.env` does not update an already-created container. Stop and remove the container, then run the command again so Podman creates a new container with the updated environment.
