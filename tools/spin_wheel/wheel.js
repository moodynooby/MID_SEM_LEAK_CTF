/**
 * Live Projector Interactive Spin Wheel Engine
 * IEEE AUSB: Case File: The Mid-Sem Leak (28/10/2026)
 * Pure Offline HTML5 Canvas + Web Audio API
 */

(function () {
  "use strict";

  // --- Default Configuration (Issue #25 Specification) ---
  const DEFAULT_CONFIG = {
    spin_duration_ms: 6000,
    min_rotations: 5,
    max_rotations: 8,
    audio_enabled: true,
    segments: [
      {
        id: "hot_sauce",
        name: "Hot Sauce Shot",
        weight: 20,
        icon: "🌶️",
        color: "#dc2626",
        textColor: "#ffffff",
        description: "One teammate eats 1 spoonful of hot sauce ➔ 1 free unpenalized hint docket awarded from Tech Leads.",
        sound: "sizzle"
      },
      {
        id: "public_intel",
        name: "Public Intel Drop",
        weight: 15,
        icon: "💡",
        color: "#2563eb",
        textColor: "#ffffff",
        description: "Host broadcasts an overarching 1-sentence clue on the projector screen for all teams.",
        sound: "chime"
      },
      {
        id: "speed_window",
        name: "5-Min Speed Window",
        weight: 15,
        icon: "⚡",
        color: "#ca8a04",
        textColor: "#000000",
        description: "If the spinning team solves any challenge within the next 5 minutes, they earn +50 bonus points.",
        sound: "fanfare"
      },
      {
        id: "keyboard_freeze",
        name: "2-Min Keyboard Freeze",
        weight: 10,
        icon: "🛑",
        color: "#991b1b",
        textColor: "#ffffff",
        description: "The entire spinning team must step back from computers for 120 seconds.",
        sound: "buzzer"
      },
      {
        id: "eliminate_decoy",
        name: "Eliminate a Decoy",
        weight: 15,
        icon: "🎭",
        color: "#7c3aed",
        textColor: "#ffffff",
        description: "Host publicly eliminates one innocent suspect profile from the case dossier board.",
        sound: "chime"
      },
      {
        id: "teammate_swap",
        name: "Teammate Role Swap",
        weight: 10,
        icon: "🔄",
        color: "#0891b2",
        textColor: "#ffffff",
        description: "Teammates swap seats and workstations for the next 10 minutes.",
        sound: "chime"
      },
      {
        id: "sweet_relief",
        name: "Sweet Relief",
        weight: 10,
        icon: "🍬",
        color: "#059669",
        textColor: "#ffffff",
        description: "A bowl of chocolates / candy delivered directly to the team's workstation.",
        sound: "fanfare"
      },
      {
        id: "sound_alarm",
        name: "Sound the Alarm",
        weight: 5,
        icon: "🚨",
        color: "#ea580c",
        textColor: "#ffffff",
        description: "Lab PA system sounds the intrusion alarm siren for 5 seconds.",
        sound: "siren"
      }
    ],
    teams: [
      "Station 1 - ByteBandits",
      "Station 2 - CipherSquad",
      "Station 3 - KernelPanic",
      "Station 4 - HashCrashers",
      "Station 5 - NullPointers",
      "Station 6 - RootNinjas",
      "Station 7 - NetStalkers",
      "Station 8 - StackSmashers",
      "Station 9 - ScriptKiddies",
      "Station 10 - GlitchHunters"
    ]
  };

  // State Management
  let config = JSON.parse(JSON.stringify(DEFAULT_CONFIG));
  let isSpinning = false;
  let currentRotation = 0; // In radians
  let spinAnimationId = null;
  let historyLogs = [];
  let hotSauceLogs = [];

  // DOM Elements
  const canvas = document.getElementById("wheel-canvas");
  const ctx = canvas.getContext("2d");
  const pointerEl = document.getElementById("wheel-pointer");
  const spinBtn = document.getElementById("spin-btn");
  const centerHub = document.getElementById("center-hub");
  const teamSelect = document.getElementById("team-select");
  const historyList = document.getElementById("history-list");
  const winnerModal = document.getElementById("winner-modal");
  const configModal = document.getElementById("config-modal");
  const hotSauceModal = document.getElementById("hotsauce-modal");
  const muteBtn = document.getElementById("mute-btn");
  const fullscreenBtn = document.getElementById("fullscreen-btn");

  // Web Audio Context (100% Offline Synthesizer)
  let audioCtx = null;
  let masterGain = null;

  function initAudio() {
    if (!audioCtx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      audioCtx = new AudioContextClass();
      masterGain = audioCtx.createGain();
      masterGain.gain.value = config.audio_enabled ? 0.7 : 0.0;
      masterGain.connect(audioCtx.destination);
    }
    if (audioCtx.state === "suspended") {
      audioCtx.resume();
    }
  }

  // Sound Synthesis Helpers
  const SOUNDS = {
    tick: function () {
      if (!config.audio_enabled || !audioCtx) return;
      const t = audioCtx.currentTime;
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(1200, t);
      osc.frequency.exponentialRampToValueAtTime(300, t + 0.02);
      gain.gain.setValueAtTime(0.4, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.02);
      osc.connect(gain);
      gain.connect(masterGain);
      osc.start(t);
      osc.stop(t + 0.03);
    },
    fanfare: function () {
      if (!config.audio_enabled || !audioCtx) return;
      const t = audioCtx.currentTime;
      [523.25, 659.25, 783.99, 1046.5].forEach((freq, i) => {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = "triangle";
        osc.frequency.value = freq;
        gain.gain.setValueAtTime(0.001, t + i * 0.1);
        gain.gain.exponentialRampToValueAtTime(0.6, t + i * 0.1 + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.001, t + i * 0.1 + 0.5);
        osc.connect(gain);
        gain.connect(masterGain);
        osc.start(t + i * 0.1);
        osc.stop(t + i * 0.1 + 0.55);
      });
    },
    buzzer: function () {
      if (!config.audio_enabled || !audioCtx) return;
      const t = audioCtx.currentTime;
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(140, t);
      osc.frequency.linearRampToValueAtTime(110, t + 0.6);
      gain.gain.setValueAtTime(0.7, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.65);
      osc.connect(gain);
      gain.connect(masterGain);
      osc.start(t);
      osc.stop(t + 0.7);
    },
    siren: function () {
      if (!config.audio_enabled || !audioCtx) return;
      const t = audioCtx.currentTime;
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = "square";
      // Oscillate frequency up and down for 2.5 seconds
      for (let i = 0; i < 5; i++) {
        osc.frequency.setValueAtTime(600, t + i * 0.5);
        osc.frequency.linearRampToValueAtTime(950, t + i * 0.5 + 0.25);
        osc.frequency.linearRampToValueAtTime(600, t + i * 0.5 + 0.5);
      }
      gain.gain.setValueAtTime(0.5, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 2.5);
      osc.connect(gain);
      gain.connect(masterGain);
      osc.start(t);
      osc.stop(t + 2.55);
    },
    sizzle: function () {
      if (!config.audio_enabled || !audioCtx) return;
      const t = audioCtx.currentTime;
      const bufferSize = Math.ceil(audioCtx.sampleRate * 0.8);
      const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) {
        data[i] = Math.random() * 2 - 1;
      }
      const noise = audioCtx.createBufferSource();
      noise.buffer = buffer;
      const filter = audioCtx.createBiquadFilter();
      filter.type = "bandpass";
      filter.frequency.value = 3200;
      const gain = audioCtx.createGain();
      gain.gain.setValueAtTime(0.4, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.8);
      noise.connect(filter);
      filter.connect(gain);
      gain.connect(masterGain);
      noise.start(t);
      noise.stop(t + 0.85);
    },
    chime: function () {
      if (!config.audio_enabled || !audioCtx) return;
      const t = audioCtx.currentTime;
      [880, 1320].forEach((freq, i) => {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = "sine";
        osc.frequency.value = freq;
        gain.gain.setValueAtTime(0.001, t + i * 0.15);
        gain.gain.exponentialRampToValueAtTime(0.5, t + i * 0.15 + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.001, t + i * 0.15 + 0.7);
        osc.connect(gain);
        gain.connect(masterGain);
        osc.start(t + i * 0.15);
        osc.stop(t + i * 0.15 + 0.75);
      });
    }
  };

  // Math & Geometry Calculation
  function getTotalWeight() {
    return config.segments.reduce((acc, s) => acc + (parseFloat(s.weight) || 0), 0);
  }

  function getSegmentAngles() {
    const totalWeight = getTotalWeight();
    const angles = [];
    let currentAngle = 0;
    config.segments.forEach(seg => {
      const sliceAngle = (seg.weight / totalWeight) * (2 * Math.PI);
      angles.push({
        segment: seg,
        startAngle: currentAngle,
        endAngle: currentAngle + sliceAngle,
        sliceAngle: sliceAngle
      });
      currentAngle += sliceAngle;
    });
    return angles;
  }

  // Draw Wheel on Canvas
  function drawWheel() {
    const dpr = window.devicePixelRatio || 1;
    const size = 620;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    ctx.scale(dpr, dpr);

    const centerX = size / 2;
    const centerY = size / 2;
    const radius = size / 2 - 15;

    ctx.clearRect(0, 0, size, size);

    // Outer Glow Ring
    ctx.save();
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius + 8, 0, 2 * Math.PI);
    ctx.strokeStyle = "rgba(125, 211, 252, 0.4)";
    ctx.lineWidth = 4;
    ctx.shadowColor = "#7dd3fc";
    ctx.shadowBlur = 18;
    ctx.stroke();
    ctx.restore();

    // Wheel Base Ring
    ctx.save();
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius + 2, 0, 2 * Math.PI);
    ctx.fillStyle = "#0c1322";
    ctx.fill();
    ctx.strokeStyle = "#1f2740";
    ctx.lineWidth = 6;
    ctx.stroke();
    ctx.restore();

    const segmentAngles = getSegmentAngles();

    // Draw Slices
    segmentAngles.forEach((item, index) => {
      const seg = item.segment;
      const start = item.startAngle + currentRotation;
      const end = item.endAngle + currentRotation;

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.arc(centerX, centerY, radius, start, end);
      ctx.closePath();
      ctx.fillStyle = seg.color;
      ctx.fill();

      // Slice Border
      ctx.strokeStyle = "rgba(5, 7, 13, 0.6)";
      ctx.lineWidth = 2.5;
      ctx.stroke();
      ctx.restore();

      // Draw Segment Text & Icon
      ctx.save();
      ctx.translate(centerX, centerY);
      const midAngle = start + (end - start) / 2;
      ctx.rotate(midAngle);

      // Icon & Name
      ctx.textAlign = "right";
      ctx.fillStyle = seg.textColor || "#ffffff";
      ctx.font = "bold 15px system-ui, sans-serif";
      ctx.shadowColor = "rgba(0, 0, 0, 0.8)";
      ctx.shadowBlur = 6;
      ctx.fillText(`${seg.icon}  ${seg.name}`, radius - 28, 5);

      // Weight badge
      ctx.font = "600 11px system-ui, monospace";
      ctx.fillStyle = "rgba(255, 255, 255, 0.75)";
      ctx.fillText(`${seg.weight}%`, radius - 30, 20);

      ctx.restore();

      // Draw Outer Peg Dot at segment boundaries
      ctx.save();
      const pegX = centerX + (radius - 2) * Math.cos(start);
      const pegY = centerY + (radius - 2) * Math.sin(start);
      ctx.beginPath();
      ctx.arc(pegX, pegY, 5, 0, 2 * Math.PI);
      ctx.fillStyle = "#f5c842";
      ctx.shadowColor = "#f5c842";
      ctx.shadowBlur = 8;
      ctx.fill();
      ctx.strokeStyle = "#000000";
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.restore();
    });
  }

  // Weighted Selection Algorithm
  function pickTargetSegment() {
    const totalWeight = getTotalWeight();
    let randomNum = Math.random() * totalWeight;
    for (let i = 0; i < config.segments.length; i++) {
      if (randomNum < config.segments[i].weight) {
        return { segment: config.segments[i], index: i };
      }
      randomNum -= config.segments[i].weight;
    }
    return { segment: config.segments[0], index: 0 };
  }

  // Ease Out Cubic Physics Curve
  function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  // Spin The Wheel
  function spin() {
    if (isSpinning) return;
    initAudio();

    const selectedTeam = teamSelect.value || "General Broadcast";
    const picked = pickTargetSegment();
    const segmentAngles = getSegmentAngles();
    const targetSlice = segmentAngles[picked.index];

    // Pointer is at the top (angle = 3 * Math.PI / 2 or -Math.PI / 2)
    // To land on targetSlice, (midSlice + finalRotation) % 2PI must align with topPointer
    const pointerAngle = (3 * Math.PI) / 2;
    // Add random jitter within slice (from 15% to 85% of slice width) to avoid always landing dead center
    const sliceJitter = targetSlice.startAngle + (targetSlice.endAngle - targetSlice.startAngle) * (0.2 + Math.random() * 0.6);
    
    // Calculate required rotations
    const spins = config.min_rotations + Math.floor(Math.random() * (config.max_rotations - config.min_rotations + 1));
    const targetNormalized = (pointerAngle - sliceJitter) % (2 * Math.PI);
    const positiveTarget = (targetNormalized + 2 * Math.PI) % (2 * Math.PI);
    
    const startAngle = currentRotation;
    const finalAngle = startAngle + (spins * 2 * Math.PI) + (positiveTarget - (startAngle % (2 * Math.PI)));

    isSpinning = true;
    spinBtn.disabled = true;
    centerHub.style.pointerEvents = "none";

    const duration = config.spin_duration_ms || 6000;
    const startTime = performance.now();
    let lastPegIndex = -1;

    function animate(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const ease = easeOutCubic(progress);

      currentRotation = startAngle + (finalAngle - startAngle) * ease;
      drawWheel();

      // Check peg crossing for physical sound tick & needle deflect
      const currentAtTop = ((pointerAngle - currentRotation) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI);
      const segmentAnglesNow = getSegmentAngles();
      for (let i = 0; i < segmentAnglesNow.length; i++) {
        const diff = Math.abs(currentAtTop - segmentAnglesNow[i].startAngle);
        if (diff < 0.08 && lastPegIndex !== i) {
          SOUNDS.tick();
          deflectPointer();
          lastPegIndex = i;
          break;
        }
      }

      if (progress < 1) {
        spinAnimationId = requestAnimationFrame(animate);
      } else {
        isSpinning = false;
        spinBtn.disabled = false;
        centerHub.style.pointerEvents = "auto";
        onSpinComplete(picked.segment, selectedTeam);
      }
    }

    spinAnimationId = requestAnimationFrame(animate);
  }

  function deflectPointer() {
    pointerEl.style.transform = "translateX(-50%) rotate(-18deg)";
    setTimeout(() => {
      pointerEl.style.transform = "translateX(-50%) rotate(0deg)";
    }, 60);
  }

  // Handle Complete Spin Event
  function onSpinComplete(segment, team) {
    // Play Outcome Sound
    if (segment.sound && SOUNDS[segment.sound]) {
      SOUNDS[segment.sound]();
    } else {
      SOUNDS.chime();
    }

    // Record in History
    const logEntry = {
      timestamp: new Date().toLocaleTimeString(),
      team: team,
      segment: segment
    };
    historyLogs.unshift(logEntry);
    updateHistoryUI();

    // Show Winner Modal
    document.getElementById("winner-icon").textContent = segment.icon;
    document.getElementById("winner-title").textContent = segment.name;
    document.getElementById("winner-team").textContent = `Selected: ${team}`;
    document.getElementById("winner-description").textContent = segment.description;
    winnerModal.classList.add("show");
  }

  function updateHistoryUI() {
    historyList.innerHTML = "";
    if (historyLogs.length === 0) {
      historyList.innerHTML = `<li class="history-item"><span style="color:var(--text-muted)">No spins recorded yet.</span></li>`;
      return;
    }
    historyLogs.slice(0, 10).forEach(log => {
      const li = document.createElement("li");
      li.className = "history-item";
      li.innerHTML = `
        <span class="item-team">${log.team}</span>
        <span class="item-segment">${log.segment.icon} ${log.segment.name}</span>
        <span class="item-time">${log.timestamp}</span>
      `;
      historyList.appendChild(li);
    });
  }

  // Populate Teams Dropdown
  function populateTeams() {
    teamSelect.innerHTML = "";
    config.teams.forEach(team => {
      const opt = document.createElement("option");
      opt.value = team;
      opt.textContent = team;
      teamSelect.appendChild(opt);
    });
  }

  // Configuration Modal Logic
  function openConfigModal() {
    const tableBody = document.getElementById("config-segments-body");
    tableBody.innerHTML = "";
    config.segments.forEach((seg, idx) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><input type="text" class="form-input" style="width:60px" value="${seg.icon}" data-idx="${idx}" data-field="icon"></td>
        <td><input type="text" class="form-input" value="${seg.name}" data-idx="${idx}" data-field="name"></td>
        <td><input type="number" class="form-input" style="width:70px" min="1" max="100" value="${seg.weight}" data-idx="${idx}" data-field="weight"></td>
        <td><input type="color" value="${seg.color}" data-idx="${idx}" data-field="color" style="cursor:pointer; height:32px; width:45px; background:transparent; border:none;"></td>
        <td><input type="text" class="form-input" value="${seg.description}" data-idx="${idx}" data-field="description"></td>
      `;
      tableBody.appendChild(tr);
    });
    document.getElementById("cfg-duration").value = config.spin_duration_ms / 1000;
    configModal.classList.add("show");
  }

  function saveConfigModal() {
    const rows = document.querySelectorAll("#config-segments-body tr");
    const newSegments = [];
    rows.forEach(tr => {
      const icon = tr.querySelector('[data-field="icon"]').value;
      const name = tr.querySelector('[data-field="name"]').value;
      const weight = parseFloat(tr.querySelector('[data-field="weight"]').value) || 10;
      const color = tr.querySelector('[data-field="color"]').value;
      const desc = tr.querySelector('[data-field="description"]').value;
      newSegments.push({
        id: name.toLowerCase().replace(/[^a-z0-9]/g, "_"),
        name: name,
        icon: icon,
        weight: weight,
        color: color,
        textColor: "#ffffff",
        description: desc
      });
    });
    config.segments = newSegments;
    config.spin_duration_ms = (parseFloat(document.getElementById("cfg-duration").value) || 6) * 1000;
    localStorage.setItem("midsem_wheel_config", JSON.stringify(config));
    drawWheel();
    configModal.classList.remove("show");
  }

  function resetConfigDefaults() {
    if (confirm("Reset wheel configuration to default specifications?")) {
      config = JSON.parse(JSON.stringify(DEFAULT_CONFIG));
      localStorage.removeItem("midsem_wheel_config");
      drawWheel();
      openConfigModal();
    }
  }

  // Hot Sauce Lifelines Tracker
  function logHotSauceHint() {
    const team = document.getElementById("hs-team-select").value;
    const challenge = document.getElementById("hs-challenge-input").value.trim() || "General Hint Docket";
    const entry = {
      time: new Date().toLocaleTimeString(),
      team: team,
      challenge: challenge
    };
    hotSauceLogs.unshift(entry);
    updateHotSauceUI();
    document.getElementById("hs-challenge-input").value = "";
  }

  function updateHotSauceUI() {
    const list = document.getElementById("hs-history-list");
    list.innerHTML = "";
    if (hotSauceLogs.length === 0) {
      list.innerHTML = `<li class="history-item"><span style="color:var(--text-muted)">No hot sauce lifelines claimed yet.</span></li>`;
      return;
    }
    hotSauceLogs.forEach(item => {
      const li = document.createElement("li");
      li.className = "history-item";
      li.innerHTML = `
        <span class="item-team">🌶️ ${item.team}</span>
        <span class="item-segment">${item.challenge}</span>
        <span class="item-time">${item.time} (0 penalty)</span>
      `;
      list.appendChild(li);
    });
  }

  // Initialization & Event Listeners
  function init() {
    // Load cached config if exists
    const cached = localStorage.getItem("midsem_wheel_config");
    if (cached) {
      try {
        config = JSON.parse(cached);
      } catch (e) {
        config = JSON.parse(JSON.stringify(DEFAULT_CONFIG));
      }
    }

    populateTeams();
    drawWheel();
    updateHistoryUI();

    // Populate Hot Sauce team dropdown
    const hsSelect = document.getElementById("hs-team-select");
    if (hsSelect) {
      hsSelect.innerHTML = teamSelect.innerHTML;
    }

    // Button Click Listeners
    spinBtn.addEventListener("click", spin);
    centerHub.addEventListener("click", spin);

    document.getElementById("close-winner-btn").addEventListener("click", () => {
      winnerModal.classList.remove("show");
    });

    document.getElementById("open-config-btn").addEventListener("click", openConfigModal);
    document.getElementById("close-config-btn").addEventListener("click", () => {
      configModal.classList.remove("show");
    });
    document.getElementById("save-config-btn").addEventListener("click", saveConfigModal);
    document.getElementById("reset-config-btn").addEventListener("click", resetConfigDefaults);

    document.getElementById("open-hotsauce-btn").addEventListener("click", () => {
      hotSauceModal.classList.add("show");
      updateHotSauceUI();
    });
    document.getElementById("close-hotsauce-btn").addEventListener("click", () => {
      hotSauceModal.classList.remove("show");
    });
    document.getElementById("hs-award-btn").addEventListener("click", logHotSauceHint);

    muteBtn.addEventListener("click", () => {
      config.audio_enabled = !config.audio_enabled;
      if (masterGain) {
        masterGain.gain.value = config.audio_enabled ? 0.7 : 0.0;
      }
      muteBtn.textContent = config.audio_enabled ? "🔊 Audio: ON" : "🔇 Audio: MUTED";
    });

    fullscreenBtn.addEventListener("click", () => {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {});
      } else {
        document.exitFullscreen().catch(() => {});
      }
    });

    // Keyboard Shortcuts
    document.addEventListener("keydown", e => {
      // Space to spin (when modal is not focused)
      if (e.code === "Space" && !winnerModal.classList.contains("show") && !configModal.classList.contains("show")) {
        e.preventDefault();
        spin();
      }
      // R to reset / close modal
      if (e.key === "r" || e.key === "R") {
        winnerModal.classList.remove("show");
        configModal.classList.remove("show");
        hotSauceModal.classList.remove("show");
      }
      // M to toggle mute
      if (e.key === "m" || e.key === "M") {
        muteBtn.click();
      }
      // F to toggle fullscreen
      if (e.key === "f" || e.key === "F") {
        fullscreenBtn.click();
      }
    });

    // Window Resize Redraw
    window.addEventListener("resize", drawWheel);
  }

  document.addEventListener("DOMContentLoaded", init);
})();
