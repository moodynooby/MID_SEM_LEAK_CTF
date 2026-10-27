# Master Live Ops Cockpit & AV Deck

Case File: The Mid-Sem Leak — IEEE AUSB CTF (28 October 2026, AU Labs 207 & 208)

The entire audio-visual experience, spin wheel gamification, intrusion monitoring, and live-event timeline controllers have been consolidated into a **Unified Master Live Ops Cockpit** served at `/av-console/`.

## Access & Security

- **LAN URL:** `http://<LAN_IP>/av-console/` (Port 80)
- **Local URL:** `http://localhost/av-console/`
- **CLI Runner:** `uv run ctf console` (or `uv run ctf ui`)
- **Access Control:** Protected by role-based authentication.
  - Automatically unlocks if logged in as a CTFd Administrator.
  - Manual unlock accepts your CTFd Admin password or `CTFD_ADMIN_TOKEN`.
  - Non-admins on the LAN cannot access controls, wheel triggers, or soundboards.

## Integrated Deck Modules

| Module | Navigation Hash | Operational Purpose |
| :--- | :--- | :--- |
| **🎡 Projector Spin Wheel** | `/av-console/#wheel` | 60fps Canvas wheel, rotational deceleration, workstation assignment, Hot Sauce Station lifelines |
| **⏱️ Big-Screen Countdown** | `/av-console/#countdown` | Real-time countdown to next milestone, 1-hour active window progress bar, 7-phase timeline |
| **🔊 Sound Cue Board** | `/av-console/#soundboard` | Synthesized Web Audio cues for Competition Start, Vanishing, Lightning, Blackout, and Reveal |
| **⚡ Live Event Actions** | `/av-console/#events` | One-click triggers for Scoreboard Blackout, Reveal, Clue Drops #1 & #2, Vanishing toggle, Theme |
| **🛠️ System Ops & Health** | `/av-console/#infra` | Container health monitor (`app`, `proxy`, `db`, `cache`), disaster recovery snapshot, standby LAN sync |

## Global Hotkeys

- `SPACE`: Spin the Projector Wheel
- `1` to `5`: Trigger Live Audio Cues (Start, Vanishing, Lightning, Blackout, Reveal)
- `M`: Toggle Master Audio Mute
- `F`: Toggle Fullscreen Mode
