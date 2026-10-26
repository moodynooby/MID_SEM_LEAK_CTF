/*
 * Scoreboard Projector Mode — activation + live solve ticker.
 *
 * Runs on every CTFd page (injected via the `theme_footer` config) but
 * only acts on /scoreboard. It:
 *   1. Adds `projector-mode` to <body> so scoreboard-projector.css takes
 *      effect, scoped to this page only.
 *   2. Polls the scoreboard table and flashes any row whose score cell
 *      changed since the last check — a lightweight "first blood /
 *      live solve" highlight that needs no CTFd internals beyond the
 *      rendered table.
 *
 * Source of truth for the `theme_footer` CTFd config. Apply with:
 *   uv run ctf theme
 * See ctfd-theme/README.md and ops/apply_scoreboard_theme.py.
 */
(function () {
  "use strict";

  function isScoreboardPage() {
    return /\/scoreboard\/?$/.test(window.location.pathname);
  }

  function watchScoreboard() {
    var table = document.querySelector("table");
    if (!table) {
      // CTFd's scoreboard table renders asynchronously after the page
      // script boots; keep retrying until it exists.
      setTimeout(watchScoreboard, 500);
      return;
    }

    var lastScores = {};

    function snapshot() {
      var rows = table.querySelectorAll("tbody tr");
      rows.forEach(function (row) {
        var cells = row.querySelectorAll("td");
        if (cells.length < 2) {
          return;
        }
        var team = cells[1].textContent.trim();
        var score = cells[cells.length - 1].textContent.trim();
        if (lastScores[team] !== undefined && lastScores[team] !== score) {
          row.classList.add("score-flash");
          setTimeout(function () {
            row.classList.remove("score-flash");
          }, 2500);
        }
        lastScores[team] = score;
      });
    }

    snapshot();
    setInterval(snapshot, 3000);
  }

  function init() {
    if (!isScoreboardPage()) {
      return;
    }
    document.body.classList.add("projector-mode");
    watchScoreboard();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
