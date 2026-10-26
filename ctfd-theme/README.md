# Scoreboard Projector Theme

Big-screen styling for CTFd's `/scoreboard` page, for the projectors in
GICT Labs 207 & 208 (issue: *Big-Screen Projector Dashboard & AV Experience*).

## What this does

- **High-contrast dark layout** with large, clamp()-scaled typography
  readable from the back of the room.
- **Medal highlighting** for the top 3 teams.
- **Live solve ticker:** any row whose score changes gets a short green
  flash, so the room visibly notices new solves as they land.
- Hides the nav/footer chrome that's irrelevant on a display nobody is
  clicking through.

It is scoped entirely to `/scoreboard` — both files only affect pages
matched by `window.location.pathname` in the JS, and the CSS only
applies under the `body.projector-mode` class that the JS adds. Login,
challenge, and admin pages are untouched.

## Files

| File | Applied as | Purpose |
| :--- | :--- | :--- |
| `scoreboard-projector.css` | CTFd `theme_header` config | Styling |
| `scoreboard-projector.js` | CTFd `theme_footer` config | Activation + live ticker |

## Why not a custom Jinja2 theme or in-container edit

CTFd officially supports exactly this kind of lightweight, per-site
CSS/JS override through the `theme_header` / `theme_footer` configs
(injected into `<head>` and before `</body>` respectively) without
forking the `core-beta` theme's Jinja2 templates — which would be
considerably more invasive for a styling-only change.

Per `AGENTS.md`, these configs live in MariaDB and are wiped by
`docker compose down -v`, and hand-editing them through the Admin UI
is exactly the "manual GUI-only, uncommitted" change the repo's
engineering pillars rule out. So the CSS/JS here are the versioned
source of truth, and `ops/apply_scoreboard_theme.py` (wired up as
`uv run ctf theme`) is the only thing that's allowed to write them.

## Applying it

```bash
uv run ctf theme
```

Run this once after any fresh `uv run ctf start` / `uv run ctf
restore`, since a from-scratch database won't have the configs set
yet. Requires `CTFD_ADMIN_TOKEN` in `.env` (see
`docs/TECH_LEAD_RUNBOOK.md`, Step 4 of the pre-event dry run).

## Editing the styling

Edit `scoreboard-projector.css` / `.js` in this directory, then re-run
`uv run ctf theme` to push the update. Do not edit the theme header/footer
fields directly in the CTFd Admin UI — that edit will be silently
overwritten the next time this script runs, and is not captured by
`uv run ctf backup`'s own file-based snapshot of this repo.
