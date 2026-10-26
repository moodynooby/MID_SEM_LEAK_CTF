# m0xblood CTFd Theme (Dark Cyberpunk / Investigation Aesthetic)

Custom dark cyberpunk theme with crimson accents for CTFd 3.7.0.
Adapted for **Case File: The Mid-Sem Leak** (IEEE AUSB CTF, 28 Oct 2026).

## Overview
- **Base Architecture:** Built on CTFd's modern `core-beta` framework (Bootstrap 5, Alpine.js, Vite).
- **Offline Campus LAN Compliant:** Contains zero external CDN script or font dependencies; all webfonts (`webfonts/`) and assets (`static/assets/`) are self-hosted locally within the theme bundle.
- **Visuals:** High-contrast dark backgrounds (`#0a0a0c`), crimson accents (`#ff1a40` / `#dc3545`), animated challenge board elements, and responsive layout.
- **Original Author:** Muhammad Osama ([0x4m4](https://github.com/0x4m4/m0xblood-ctfd-theme)), licensed under MIT.

## Integration & Deployment
- Declaratively mounted into the CTFd container via `docker-compose.yml`:
  ```yaml
  volumes:
    - ./themes/m0xblood:/opt/CTFd/CTFd/themes/m0xblood:ro
  ```
- Activated and synchronized via the unified CLI:
  ```bash
  uv run ctf theme
  ```
