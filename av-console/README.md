# AV Console

Static pages for running the big-screen AV experience during the
competition (issue: *Big-Screen Projector Dashboard & AV Experience*).
No backend, no build step, no external audio/image assets — pure
HTML/CSS/JS so it's reproducible offline on the lab LAN like everything
else in this repo.

| Page | Who opens it | Purpose |
| :--- | :--- | :--- |
| `countdown.html` | Projector screen | Fullscreen countdown through the 4:30-5:30 PM milestone timeline |
| `soundboard.html` | Tech Lead console laptop | Fires the 5 live-event sound cues from the runbook |

The CTFd scoreboard itself is styled separately — see
[`../ctfd-theme/`](../ctfd-theme/).

## Opening the pages

Nginx serves this directory on the LAN alongside CTFd, so any device
(the projector PC, a Tech Lead's laptop) can reach it without file
copying:

```
http://<LAN_IP>/av-console/countdown.html
http://<LAN_IP>/av-console/soundboard.html
```

Opening the `.html` files directly (`file://`) also works, since there's
no server-side logic — handy for testing before `uv run ctf start`.

### Countdown clock

- Press `F11` on the projector PC to go fullscreen.
- Automatically advances through every milestone in
  `docs/TECH_LEAD_RUNBOOK.md` and shows time remaining to the next one,
  plus an overall progress bar.
- For the 27 Oct dry run, use the query params to rehearse the full
  timeline in fast-forward instead of waiting for the real clock:
  - `?date=2026-10-27` — run it against the dry-run date
  - `?offset=<minutes>` — shift every milestone by N minutes (e.g.
    `?offset=-90` to pull the whole timeline 90 minutes earlier so it
    starts immediately)

### Sound cue board

Five buttons (and keys `1`-`5`) matching the runbook's milestones.
Every cue is synthesized live with the Web Audio API — there are no
`.mp3`/`.wav` files to source, license, or keep in sync — so the board
works fully offline and the "sound" is entirely defined by
`soundboard.js`. Includes a volume slider and a "Stop All" kill switch,
and logs the last cue fired so the Tech Lead can confirm it went off
even over room noise.

| Cue | Milestone |
| :--- | :--- |
| 🎉 Competition Start | 4:30 PM |
| 📡 Vanishing Challenge | 4:35 PM |
| ⚡ Lightning Round | 5:00 PM |
| 🌑 Scoreboard Blackout | 5:15 PM |
| 🏆 Scoreboard Reveal | 5:30 PM |

Browsers require a user gesture before `AudioContext` can play sound —
the first button click on the page primes it, so do one test click
before going live.
