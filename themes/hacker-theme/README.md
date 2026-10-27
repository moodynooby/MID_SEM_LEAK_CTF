# CTFd Hacker Theme (Official Green Terminal Aesthetic)

Official CTFd Hacker Theme with high-contrast phosphor green (`#b5e853`) typography and deep dark terminal surfaces (`#212529`).
Deployed for **Case File: The Mid-Sem Leak** (IEEE AUSB CTF, 28 Oct 2026).

## Overview
- **Base Framework:** CTFd `core-beta` architecture with Bootstrap 5, Alpine.js, and Vite bundling.
- **Offline Campus LAN Compliant:** Contains zero external CDN script or font dependencies; all webfonts (`webfonts/` including Red Hat Mono and FontAwesome) and assets (`static/assets/`) are self-hosted locally within the theme bundle.
- **Visuals:** High-contrast dark backgrounds, phosphor lime accents (`#b5e853` / `#91ba42`), terminal monospace typography, and responsive layout.
- **Source:** Extracted directly from official CTFd demo instance (`demo.ctfd.io`).

## Integration & Deployment
- Declaratively mounted into the CTFd container via `docker-compose.yml`:
  ```yaml
  volumes:
    - ./themes/hacker-theme:/opt/CTFd/CTFd/themes/hacker-theme:ro
  ```
- Activated and synchronized via the unified CLI:
  ```bash
  uv run ctf theme
  ```
