/*
 * Fullscreen projector countdown clock.
 *
 * Walks the live-event timeline from docs/TECH_LEAD_RUNBOOK.md and
 * always shows: time remaining to the *next* milestone, the overall
 * event progress bar, and a tick list of what's already happened.
 *
 * Query params (for the 27 Oct dry run / rehearsal, see runbook):
 *   ?date=YYYY-MM-DD   - override the event date (default: 2026-10-28)
 *   ?offset=<minutes>  - shift every milestone by N minutes, so you can
 *                        rehearse the whole timeline in fast-forward
 *                        without waiting for the real clock
 */
(function () {
  "use strict";

  var DEFAULT_DATE = "2026-10-28";

  var MILESTONES = [
    { time: "16:30", label: "Competition Start" },
    { time: "16:35", label: "Vanishing Challenge Opens" },
    { time: "16:45", label: "Clue Drop #1" },
    { time: "16:50", label: "Vanishing Challenge Closes" },
    { time: "17:00", label: "Lightning Round Begins" },
    { time: "17:10", label: "Lightning Round Ends / Clue Drop #2" },
    { time: "17:15", label: "Scoreboard Blackout" },
    { time: "17:30", label: "Scoreboard Reveal — Event Ends" },
  ];

  function params() {
    return new URLSearchParams(window.location.search);
  }

  function buildSchedule() {
    var p = params();
    var dateStr = p.get("date") || DEFAULT_DATE;
    var offsetMin = parseInt(p.get("offset"), 10) || 0;

    return MILESTONES.map(function (m) {
      var parts = m.time.split(":");
      var d = new Date(dateStr + "T00:00:00");
      d.setHours(parseInt(parts[0], 10), parseInt(parts[1], 10) + offsetMin, 0, 0);
      return { at: d, label: m.label };
    });
  }

  function formatDuration(ms) {
    var sign = ms < 0 ? "-" : "";
    ms = Math.abs(ms);
    var totalSeconds = Math.floor(ms / 1000);
    var h = Math.floor(totalSeconds / 3600);
    var m = Math.floor((totalSeconds % 3600) / 60);
    var s = totalSeconds % 60;
    var out = [];
    if (h > 0) {
      out.push(String(h).padStart(2, "0"));
    }
    out.push(String(m).padStart(2, "0"));
    out.push(String(s).padStart(2, "0"));
    return sign + out.join(":");
  }

  function render(schedule) {
    var now = new Date();
    var start = schedule[0].at;
    var end = schedule[schedule.length - 1].at;

    var next = schedule.find(function (m) {
      return m.at.getTime() > now.getTime();
    });

    var bigTimer = document.getElementById("big-timer");
    var nextLabel = document.getElementById("next-label");
    var wallClock = document.getElementById("wall-clock");
    var progressFill = document.getElementById("progress-fill");
    var timeline = document.getElementById("timeline");

    wallClock.textContent = now.toLocaleTimeString();

    if (now.getTime() < start.getTime()) {
      bigTimer.textContent = formatDuration(start.getTime() - now.getTime());
      nextLabel.textContent = "Until " + schedule[0].label;
    } else if (!next) {
      bigTimer.textContent = "00:00:00";
      nextLabel.textContent = "Event Complete";
    } else {
      bigTimer.textContent = formatDuration(next.at.getTime() - now.getTime());
      nextLabel.textContent = "Until " + next.label;
    }

    var progress = Math.min(
      1,
      Math.max(0, (now.getTime() - start.getTime()) / (end.getTime() - start.getTime()))
    );
    progressFill.style.width = (progress * 100).toFixed(1) + "%";

    timeline.innerHTML = "";
    schedule.forEach(function (m) {
      var done = m.at.getTime() <= now.getTime();
      var li = document.createElement("li");
      li.className = done ? "done" : "";
      li.innerHTML =
        "<span class='dot'></span><span class='time'>" +
        m.at.toTimeString().slice(0, 5) +
        "</span><span class='label'>" +
        m.label +
        "</span>";
      timeline.appendChild(li);
    });
  }

  function start() {
    var schedule = buildSchedule();
    render(schedule);
    setInterval(function () {
      render(schedule);
    }, 1000);
  }

  document.addEventListener("DOMContentLoaded", start);
})();
