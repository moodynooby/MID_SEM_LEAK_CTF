/**
 * Master Live Ops Cockpit & AV Console Engine
 * Case File: The Mid-Sem Leak — IEEE AUSB CTF (28/10/2026)
 * Pure Offline HTML5 Canvas + Web Audio API + REST Ops Engine
 */

(function () {
  "use strict";

  // --- Configuration & Constants ---
  const DEFAULT_DATE = "2026-10-28";
  const MILESTONES = [
    { time: "16:30", label: "Competition Start", key: "start" },
    { time: "16:35", label: "Vanishing Challenge Opens", key: "vanishing_start" },
    { time: "16:45", label: "Intel Clue Drop #1 & Wheel R1", key: "clue_1" },
    { time: "16:50", label: "Vanishing Challenge Closes", key: "vanishing_end" },
    { time: "17:00", label: "Lightning Round (2x) & Wheel R2", key: "lightning_start" },
    { time: "17:10", label: "Lightning Round Ends & Clue #2", key: "clue_2" },
    { time: "17:15", label: "Scoreboard Blackout (Suspense)", key: "blackout" },
    { time: "17:30", label: "Scoreboard Reveal — Event Ends", key: "reveal" },
  ];

  const DEFAULT_WHEEL_CONFIG = {
    spin_duration_ms: 6000,
    min_rotations: 5,
    max_rotations: 8,
    audio_enabled: true,
    segments: [
      { id: "hot_sauce", name: "Hot Sauce Shot", weight: 25, icon: "🌶️", color: "#dc2626", textColor: "#ffffff", desc: "One teammate eats 1 spoonful of hot sauce ➔ 1 free unpenalized hint docket." },
      { id: "public_intel", name: "Public Intel Drop", weight: 15, icon: "💡", color: "#2563eb", textColor: "#ffffff", desc: "Host broadcasts an overarching 1-sentence clue on projector screen for all teams." },
      { id: "speed_window", name: "5-Min Speed Window", weight: 15, icon: "⚡", color: "#ca8a04", textColor: "#000000", desc: "If spinning team solves any challenge within 5 minutes, they earn +50 bonus pts." },
      { id: "keyboard_freeze", name: "2-Min Keyboard Freeze", weight: 10, icon: "🛑", color: "#991b1b", textColor: "#ffffff", desc: "The entire spinning team steps back from computers for 120 seconds." },
      { id: "eliminate_decoy", name: "Eliminate a Decoy", weight: 1, icon: "🎭", color: "#7c3aed", textColor: "#ffffff", desc: "Host publicly eliminates one innocent suspect profile from case dossier board." },
      { id: "teammate_swap", name: "Teammate Role Swap", weight: 10, icon: "🔄", color: "#0d9488", textColor: "#ffffff", desc: "Two teammates swap forensic roles (e.g. Reverse Eng ⇄ PCAP Forensics) for 10m." },
      { id: "sound_theme", name: "Custom Soundtrack", weight: 14, icon: "🎵", color: "#db2777", textColor: "#ffffff", desc: "Team selects 3-minute hype or suspense soundtrack over Lab PA speakers." },
      { id: "wildcard_blank", name: "The Blank Docket", weight: 10, icon: "🃏", color: "#475569", textColor: "#ffffff", desc: "Nothing happens! The case dossier remains unchanged." }
    ]
  };

  // State
  let isAuthenticated = false;
  let authToken = sessionStorage.getItem("midsem_ops_token") || "";
  let audioMuted = false;
  let activeNodes = [];
  let audioCtx = null;
  let masterGain = null;
  let isSpinning = false;
  let currentRotation = 0;
  let spinAnimationId = null;
  let historyLogs = [];
  let alertPollingInterval = null;

  // --- Audio Synthesis Engine ---
  function getAudioContext() {
    if (!audioCtx) {
      const AudioClass = window.AudioContext || window.webkitAudioContext;
      audioCtx = new AudioClass();
      masterGain = audioCtx.createGain();
      masterGain.gain.value = audioMuted ? 0.0 : 0.6;
      masterGain.connect(audioCtx.destination);
    }
    if (audioCtx.state === "suspended") {
      audioCtx.resume();
    }
    return audioCtx;
  }

  function trackNode(node) {
    activeNodes.push(node);
    return node;
  }

  function tone(freq, startTime, duration, type) {
    if (audioMuted) return;
    const c = getAudioContext();
    const osc = c.createOscillator();
    const gain = c.createGain();
    osc.type = type || "sine";
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(0.0001, startTime);
    gain.gain.exponentialRampToValueAtTime(0.8, startTime + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, startTime + duration);
    osc.connect(gain);
    gain.connect(masterGain);
    osc.start(startTime);
    osc.stop(startTime + duration + 0.05);
    trackNode(osc);
  }

  const SOUND_CUES = {
    start: function () {
      const c = getAudioContext();
      const t = c.currentTime;
      [261.63, 329.63, 392.0, 523.25].forEach((f, i) => tone(f, t + i * 0.12, 0.5, "triangle"));
      tone(523.25, t + 0.55, 1.2, "sawtooth");
      logConsole("🔊 Played Sound Cue: [1] Competition Start Fanfare");
    },
    vanishing: function () {
      const c = getAudioContext();
      const t = c.currentTime;
      tone(900, t, 0.4, "sine");
      tone(1200, t + 0.4, 0.8, "sine");
      logConsole("🔊 Played Sound Cue: [2] Vanishing Radar Ping");
    },
    lightning: function () {
      const c = getAudioContext();
      const t = c.currentTime;
      [220, 277, 330, 440, 554, 660, 880].forEach((f, i) => tone(f, t + i * 0.07, 0.25, "sawtooth"));
      logConsole("🔊 Played Sound Cue: [3] Lightning Round Surge");
    },
    blackout: function () {
      const c = getAudioContext();
      const t = c.currentTime;
      tone(80, t, 2.5, "sawtooth");
      tone(55, t + 0.5, 3.0, "sine");
      logConsole("🔊 Played Sound Cue: [4] Scoreboard Blackout Drone");
    },
    reveal: function () {
      const c = getAudioContext();
      const t = c.currentTime;
      [261.63, 329.63, 392.0, 440.0, 523.25, 659.25, 783.99].forEach((f, i) => tone(f, t + i * 0.1, 0.6, "triangle"));
      tone(783.99, t + 0.8, 1.8, "sawtooth");
      logConsole("🔊 Played Sound Cue: [5] Scoreboard Reveal Victory");
    },
    tick: function () {
      if (audioMuted) return;
      const c = getAudioContext();
      const t = c.currentTime;
      const osc = c.createOscillator();
      const gain = c.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(1200, t);
      osc.frequency.exponentialRampToValueAtTime(300, t + 0.02);
      gain.gain.setValueAtTime(0.3, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.02);
      osc.connect(gain);
      gain.connect(masterGain);
      osc.start(t);
      osc.stop(t + 0.025);
    },
    win: function () {
      if (audioMuted) return;
      const c = getAudioContext();
      const t = c.currentTime;
      [523.25, 659.25, 783.99, 1046.5].forEach((f, i) => tone(f, t + i * 0.1, 0.4, "triangle"));
    }
  };

  function stopAllAudio() {
    activeNodes.forEach(node => {
      try { node.stop(); } catch (e) {}
    });
    activeNodes = [];
    logConsole("⏹️ All audio playback stopped.");
  }

  // --- Authentication Handling ---
  async function checkAuth() {
    const authGate = document.getElementById("auth-gate");
    
    // 1. Check existing session token
    if (authToken) {
      try {
        const res = await fetch("/api/ops/verify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token: authToken, password: authToken, pin: authToken })
        });
        const data = await res.json();
        if (data.authenticated) {
          unlockCockpit();
          return;
        }
      } catch (e) {}
    }

    // 2. Check CTFd admin session cookie (/api/v1/configs returns 200 strictly for CTFd Admins)
    try {
      const res = await fetch("/api/v1/configs", {
        credentials: "include",
        headers: { "Accept": "application/json" }
      });
      if (res.ok && res.status === 200) {
        const json = await res.json();
        if (json.success) {
          unlockCockpit();
          return;
        }
      }
    } catch (e) {}

    // Not authenticated -> show lock gate
    authGate.style.display = "flex";
  }

  function unlockCockpit() {
    isAuthenticated = true;
    document.getElementById("auth-gate").style.display = "none";
    logConsole("🛡️ Access Granted: Organizer session authenticated.");
    initTimeline();
    initWheel();
    initTeamsDropdown();
    startAlertMonitor();
    fetchInfraStatus();
  }

  // --- Console Log Helper ---
  function logConsole(msg) {
    const logBox = document.getElementById("console-log");
    if (!logBox) return;
    const time = new Date().toLocaleTimeString("en-US", { hour12: false });
    const p = document.createElement("div");
    p.textContent = `[${time}] ${msg}`;
    logBox.prepend(p);
  }

  // --- Tab Navigation ---
  function setupTabs() {
    const tabs = document.querySelectorAll(".deck-tab");
    tabs.forEach(tab => {
      tab.addEventListener("click", () => {
        const view = tab.getAttribute("data-tab");
        switchView(view);
      });
    });

    const hash = window.location.hash.replace("#", "");
    if (["wheel", "countdown", "soundboard", "events", "infra"].includes(hash)) {
      switchView(hash);
    }
  }

  function switchView(viewName) {
    document.querySelectorAll(".deck-tab").forEach(t => {
      t.classList.toggle("active", t.getAttribute("data-tab") === viewName);
    });
    document.querySelectorAll(".view-panel").forEach(p => {
      p.classList.toggle("active", p.id === `view-${viewName}`);
    });
    window.location.hash = viewName;
  }

  // --- HUD Time & Milestone Timeline Engine ---
  function initTimeline() {
    function updateClocks() {
      const now = new Date();
      const clockEl = document.getElementById("hud-clock-time");
      if (clockEl) {
        clockEl.textContent = now.toLocaleTimeString("en-US", { hour12: false });
      }

      // Build today's schedule
      const dateStr = DEFAULT_DATE;
      const schedule = MILESTONES.map(m => {
        const [h, min] = m.time.split(":");
        const d = new Date(`${dateStr}T00:00:00`);
        d.setHours(parseInt(h, 10), parseInt(min, 10), 0, 0);
        return { at: d, label: m.label, timeStr: m.time, key: m.key };
      });

      // Find upcoming milestone
      let nextMilestone = null;
      for (const item of schedule) {
        if (now < item.at) {
          nextMilestone = item;
          break;
        }
      }

      const milestonePill = document.getElementById("hud-milestone-text");
      const bigTimer = document.getElementById("big-timer-digits");
      const nextLabel = document.getElementById("countdown-next-label");

      if (nextMilestone) {
        const diffMs = nextMilestone.at - now;
        const totalSec = Math.floor(diffMs / 1000);
        const m = Math.floor(totalSec / 60);
        const s = totalSec % 60;
        const timeStr = `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
        
        if (milestonePill) milestonePill.textContent = `Next: ${nextMilestone.label} (${timeStr})`;
        if (bigTimer) bigTimer.textContent = timeStr;
        if (nextLabel) nextLabel.textContent = `NEXT: ${nextMilestone.label.toUpperCase()}`;
      } else {
        if (milestonePill) milestonePill.textContent = "Competition Closed";
        if (bigTimer) bigTimer.textContent = "00:00";
        if (nextLabel) nextLabel.textContent = "EVENT TERMINATED";
      }

      // Progress Fill across the 1-hour active window (16:30 - 17:30)
      const startT = new Date(`${dateStr}T16:30:00`).getTime();
      const endT = new Date(`${dateStr}T17:30:00`).getTime();
      const nowT = now.getTime();
      let pct = 0;
      if (nowT >= endT) pct = 100;
      else if (nowT > startT) pct = ((nowT - startT) / (endT - startT)) * 100;
      const fillBar = document.getElementById("countdown-progress-fill");
      if (fillBar) fillBar.style.width = `${pct}%`;

      // Update timeline grid cards
      schedule.forEach((item, idx) => {
        const card = document.getElementById(`timeline-card-${idx}`);
        if (!card) return;
        if (now >= item.at) {
          card.classList.add("done");
          card.classList.remove("active");
        } else if (item === nextMilestone) {
          card.classList.add("active");
          card.classList.remove("done");
        } else {
          card.classList.remove("active", "done");
        }
      });
    }

    updateClocks();
    setInterval(updateClocks, 1000);
  }

  // --- Spin Wheel Engine ---
  function initWheel() {
    const canvas = document.getElementById("wheel-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const segments = DEFAULT_WHEEL_CONFIG.segments;
    const totalWeight = segments.reduce((acc, s) => acc + s.weight, 0);

    let calculatedSegments = [];
    let curAngle = 0;
    segments.forEach(seg => {
      const sliceAngle = (seg.weight / totalWeight) * 2 * Math.PI;
      calculatedSegments.push({
        ...seg,
        startAngle: curAngle,
        endAngle: curAngle + sliceAngle,
        midAngle: curAngle + sliceAngle / 2
      });
      curAngle += sliceAngle;
    });

    function drawWheel() {
      const w = canvas.width;
      const h = canvas.height;
      const centerX = w / 2;
      const centerY = h / 2;
      const radius = w / 2 - 12;

      ctx.clearRect(0, 0, w, h);
      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.rotate(currentRotation);

      calculatedSegments.forEach(seg => {
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.arc(0, 0, radius, seg.startAngle, seg.endAngle);
        ctx.closePath();
        ctx.fillStyle = seg.color;
        ctx.fill();
        ctx.lineWidth = 2.5;
        ctx.strokeStyle = "#ffffff";
        ctx.stroke();

        ctx.save();
        ctx.rotate(seg.midAngle);
        ctx.textAlign = "right";
        ctx.fillStyle = seg.textColor;
        ctx.font = "bold 16px -apple-system, sans-serif";
        ctx.fillText(`${seg.icon} ${seg.name}`, radius - 25, 6);
        ctx.restore();
      });

      ctx.restore();
    }

    drawWheel();

    // Spin Trigger
    let lastSegmentIdx = -1;
    function triggerSpin() {
      if (isSpinning) return;
      isSpinning = true;
      const spinBtn = document.getElementById("spin-btn");
      if (spinBtn) spinBtn.disabled = true;

      // Random target calculation
      const duration = DEFAULT_WHEEL_CONFIG.spin_duration_ms;
      const extraSpins = (DEFAULT_WHEEL_CONFIG.min_rotations + Math.random() * 3) * 2 * Math.PI;
      const randOffset = Math.random() * 2 * Math.PI;
      const totalDelta = extraSpins + randOffset;
      const startRot = currentRotation;
      const targetRot = startRot + totalDelta;
      const startTime = performance.now();

      function animate(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const ease = 1 - Math.pow(1 - progress, 3);
        currentRotation = startRot + ease * totalDelta;
        drawWheel();

        // Check tick
        const normRot = (3 * Math.PI / 2 - (currentRotation % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
        const curSegIdx = calculatedSegments.findIndex(s => normRot >= s.startAngle && normRot < s.endAngle);
        if (curSegIdx !== lastSegmentIdx && curSegIdx !== -1) {
          SOUND_CUES.tick();
          lastSegmentIdx = curSegIdx;
        }

        if (progress < 1) {
          spinAnimationId = requestAnimationFrame(animate);
        } else {
          isSpinning = false;
          if (spinBtn) spinBtn.disabled = false;
          finishSpin(calculatedSegments[curSegIdx]);
        }
      }

      spinAnimationId = requestAnimationFrame(animate);
    }

    function finishSpin(winner) {
      if (!winner) return;
      SOUND_CUES.win();
      const teamSelect = document.getElementById("team-select");
      const teamName = teamSelect ? teamSelect.value : "Station Alpha";
      
      logConsole(`🎡 Spin Outcome: [${teamName}] ➔ ${winner.icon} ${winner.name}`);
      
      // Update history list
      const histList = document.getElementById("history-list");
      if (histList) {
        const li = document.createElement("li");
        li.className = "history-item";
        li.innerHTML = `<span><strong>${teamName}:</strong> ${winner.icon} ${winner.name}</span><small style="color:var(--text-muted)">${new Date().toLocaleTimeString()}</small>`;
        histList.prepend(li);
      }

      // Show winner modal
      const modal = document.getElementById("winner-modal");
      if (modal) {
        document.getElementById("winner-team-name").textContent = teamName;
        document.getElementById("winner-segment-name").textContent = `${winner.icon} ${winner.name}`;
        document.getElementById("winner-segment-desc").textContent = winner.desc;
        modal.style.display = "flex";
      }
    }

    const spinBtn = document.getElementById("spin-btn");
    if (spinBtn) spinBtn.addEventListener("click", triggerSpin);
    const centerHub = document.getElementById("center-hub");
    if (centerHub) centerHub.addEventListener("click", triggerSpin);

    // Keyboard Spacebar for Spin
    window.addEventListener("keydown", e => {
      if (e.code === "Space" && !["INPUT", "TEXTAREA", "SELECT"].includes(e.target.tagName)) {
        e.preventDefault();
        triggerSpin();
      }
    });
  }

  // --- Populate Teams Dropdown ---
  async function initTeamsDropdown() {
    const sel = document.getElementById("team-select");
    if (!sel) return;
    sel.innerHTML = "";
    
    try {
      const res = await fetch("/api/v1/teams");
      if (res.ok) {
        const json = await res.json();
        if (json.data && json.data.length > 0) {
          json.data.forEach(t => {
            const opt = document.createElement("option");
            opt.value = t.name;
            opt.textContent = `${t.name} (Team ID: ${t.id})`;
            sel.appendChild(opt);
          });
          return;
        }
      }
    } catch (e) {}

    // Fallback default teams
    for (let i = 1; i <= 20; i++) {
      const opt = document.createElement("option");
      opt.value = `Station ${i}`;
      opt.textContent = `Station ${i} — Workstation PC-${String(i).padStart(2, "0")}`;
      sel.appendChild(opt);
    }
  }

  // --- Intrusion Siren Polling ---
  function startAlertMonitor() {
    if (alertPollingInterval) clearInterval(alertPollingInterval);

    async function checkAlert() {
      try {
        const res = await fetch("/av-console/active_alert.json?t=" + Date.now());
        if (!res.ok) return;
        const data = await res.json();
        const banner = document.getElementById("siren-banner");
        const sirenText = document.getElementById("siren-banner-text");

        if (data.active && data.sound_siren) {
          if (banner) banner.style.display = "flex";
          if (sirenText) sirenText.textContent = `🚨 INTRUSION LOCKOUT: ${data.team_name} — ${data.reason}`;
        } else {
          if (banner) banner.style.display = "none";
        }
      } catch (e) {}
    }

    checkAlert();
    alertPollingInterval = setInterval(checkAlert, 2500);
  }

  // --- Event Action Handlers (CLI-to-UI) ---
  window.triggerEventAction = async function (actionKey) {
    logConsole(`⚡ Triggering Event Action: ${actionKey}...`);
    try {
      const res = await fetch(`/api/ops/${actionKey}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${authToken}`
        }
      });
      const data = await res.json();
      if (data.success || res.ok) {
        logConsole(`✅ Success: ${data.message || actionKey}`);
        alert(`Action Success: ${data.message || actionKey}`);
      } else {
        logConsole(`⚠️ Response: ${data.error || "Failed"}`);
        alert(`Error: ${data.error || "Action failed"}`);
      }
    } catch (e) {
      logConsole(`❌ Error executing ${actionKey}: ${e.message}`);
      alert(`API Error: ${e.message}`);
    }
  };

  // --- Infrastructure Status & Actions ---
  async function fetchInfraStatus() {
    try {
      const res = await fetch("/api/ops/status", {
        headers: { "Authorization": `Bearer ${authToken}` }
      });
      if (!res.ok) return;
      const data = await res.json();
      
      const badgeApp = document.getElementById("status-ctfd-app");
      const badgeProxy = document.getElementById("status-ctfd-proxy");
      const badgeDb = document.getElementById("status-ctfd-db");
      const badgeCache = document.getElementById("status-ctfd-cache");
      const lastBackupEl = document.getElementById("status-last-backup");

      if (data.containers) {
        if (badgeApp) updateBadge(badgeApp, data.containers.ctfd_app);
        if (badgeProxy) updateBadge(badgeProxy, data.containers.ctfd_proxy);
        if (badgeDb) updateBadge(badgeDb, data.containers.ctfd_db);
        if (badgeCache) updateBadge(badgeCache, data.containers.ctfd_cache);
      }

      if (lastBackupEl && data.last_backup) {
        lastBackupEl.textContent = data.last_backup;
      }
    } catch (e) {}
  }

  function updateBadge(el, status) {
    el.textContent = status || "unknown";
    if (status === "running") {
      el.style.background = "rgba(34, 197, 94, 0.2)";
      el.style.color = "var(--accent-green)";
    } else {
      el.style.background = "rgba(239, 68, 68, 0.2)";
      el.style.color = "var(--accent-red)";
    }
  }

  window.triggerBackup = async function () {
    logConsole("💾 Creating snapshot backup...");
    await window.triggerEventAction("backup");
    fetchInfraStatus();
  };

  window.triggerSync = async function () {
    const ip = prompt("Enter Standby Laptop LAN IP (e.g. 192.168.1.150):");
    if (!ip) return;
    logConsole(`🔄 Syncing latest snapshot to standby laptop at ${ip}...`);
    try {
      const res = await fetch("/api/ops/sync", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${authToken}`
        },
        body: JSON.stringify({ target_ip: ip })
      });
      const data = await res.json();
      logConsole(data.success ? `✅ Sync complete: ${data.message}` : `❌ Sync failed: ${data.error}`);
      alert(data.success ? `Sync Complete: ${data.message}` : `Error: ${data.error}`);
    } catch (e) {
      logConsole(`❌ Sync request failed: ${e.message}`);
    }
  };

  // --- Keyboard Shortcuts & Global Actions ---
  function setupGlobalControls() {
    // Soundboard cues keys 1-5
    window.addEventListener("keydown", e => {
      if (["INPUT", "TEXTAREA", "SELECT"].includes(e.target.tagName)) return;
      if (e.key === "1") SOUND_CUES.start();
      else if (e.key === "2") SOUND_CUES.vanishing();
      else if (e.key === "3") SOUND_CUES.lightning();
      else if (e.key === "4") SOUND_CUES.blackout();
      else if (e.key === "5") SOUND_CUES.reveal();
      else if (e.key === "m" || e.key === "M") toggleMute();
      else if (e.key === "f" || e.key === "F") toggleFullscreen();
    });

    const muteBtn = document.getElementById("mute-toggle-btn");
    if (muteBtn) {
      muteBtn.addEventListener("click", toggleMute);
    }

    const fsBtn = document.getElementById("fs-toggle-btn");
    if (fsBtn) {
      fsBtn.addEventListener("click", toggleFullscreen);
    }

    // Modal dismissals
    document.querySelectorAll(".close-modal-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".modal-overlay").forEach(m => m.style.display = "none");
      });
    });

    // Auth submit
    const authBtn = document.getElementById("auth-submit-btn");
    const authInput = document.getElementById("auth-pass-input");
    const authError = document.getElementById("auth-error-msg");

    if (authBtn && authInput) {
      const submitAuth = async () => {
        const val = authInput.value.trim();
        if (!val) return;
        try {
          const res = await fetch("/api/ops/verify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token: val, password: val, pin: val })
          });
          const data = await res.json();
          if (data.authenticated) {
            authToken = val;
            sessionStorage.setItem("midsem_ops_token", val);
            unlockCockpit();
          } else {
            authError.style.display = "block";
            authError.textContent = "Invalid CTFd administrator password or token.";
          }
        } catch (e) {
          authError.style.display = "block";
          authError.textContent = "Verification request failed.";
        }
      };

      authBtn.addEventListener("click", submitAuth);
      authInput.addEventListener("keydown", e => {
        if (e.key === "Enter") submitAuth();
      });
    }

    // Soundboard button clicks
    document.querySelectorAll(".sound-cue-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const cue = btn.getAttribute("data-cue");
        if (SOUND_CUES[cue]) SOUND_CUES[cue]();
      });
    });
  }

  function toggleMute() {
    audioMuted = !audioMuted;
    if (masterGain) {
      masterGain.gain.value = audioMuted ? 0.0 : 0.6;
    }
    const btn = document.getElementById("mute-toggle-btn");
    if (btn) btn.innerHTML = audioMuted ? "🔇 Audio: OFF" : "🔊 Audio: ON";
    logConsole(audioMuted ? "🔇 Audio muted" : "🔊 Audio unmuted");
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  }

  // Expose sound helpers
  window.SOUND_CUES = SOUND_CUES;
  window.stopAllAudio = stopAllAudio;

  // Init on DOM ready
  document.addEventListener("DOMContentLoaded", () => {
    setupTabs();
    setupGlobalControls();
    checkAuth();
  });
})();
