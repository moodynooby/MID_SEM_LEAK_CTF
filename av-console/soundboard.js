/*
 * Live-ops sound cue board.
 *
 * Every cue is synthesized on the fly with the Web Audio API — no
 * audio assets to source, license, or ship. That keeps this page
 * self-contained and fully reproducible offline, matching the rest of
 * the repo's "zero cloud, declarative, no binary blobs" approach.
 *
 * Keyboard shortcuts 1-5 fire the same cues as the buttons, so a Tech
 * Lead doesn't need a precise click under live-event pressure.
 */
(function () {
  "use strict";

  var ctx = null;
  var activeNodes = [];
  var masterGain = null;

  function getContext() {
    if (!ctx) {
      ctx = new (window.AudioContext || window.webkitAudioContext)();
      masterGain = ctx.createGain();
      masterGain.gain.value = 0.6;
      masterGain.connect(ctx.destination);
    }
    if (ctx.state === "suspended") {
      ctx.resume();
    }
    return ctx;
  }

  function track(node) {
    activeNodes.push(node);
    return node;
  }

  function tone(freq, startTime, duration, type) {
    var c = getContext();
    var osc = c.createOscillator();
    var gain = c.createGain();
    osc.type = type || "sine";
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(0.0001, startTime);
    gain.gain.exponentialRampToValueAtTime(0.9, startTime + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, startTime + duration);
    osc.connect(gain);
    gain.connect(masterGain);
    osc.start(startTime);
    osc.stop(startTime + duration + 0.05);
    track(osc);
    return osc;
  }

  function noiseBurst(startTime, duration) {
    var c = getContext();
    var bufferSize = Math.ceil(c.sampleRate * duration);
    var buffer = c.createBuffer(1, bufferSize, c.sampleRate);
    var data = buffer.getChannelData(0);
    for (var i = 0; i < bufferSize; i++) {
      data[i] = Math.random() * 2 - 1;
    }
    var source = c.createBufferSource();
    source.buffer = buffer;
    var gain = c.createGain();
    gain.gain.setValueAtTime(0.5, startTime);
    gain.gain.exponentialRampToValueAtTime(0.001, startTime + duration);
    source.connect(gain);
    gain.connect(masterGain);
    source.start(startTime);
    track(source);
    return source;
  }

  var CUES = {
    start: function () {
      // Competition start fanfare: ascending major triad.
      var c = getContext();
      var now = c.currentTime;
      [523.25, 659.25, 783.99, 1046.5].forEach(function (freq, i) {
        tone(freq, now + i * 0.12, 0.35, "triangle");
      });
    },
    vanishing: function () {
      // Radar ping: three short beeps with increasing gaps, like a sweep.
      var c = getContext();
      var now = c.currentTime;
      [0, 0.4, 0.9].forEach(function (offset) {
        tone(880, now + offset, 0.12, "sine");
      });
    },
    lightning: function () {
      // High-energy sweep: fast rising sawtooth stabs.
      var c = getContext();
      var now = c.currentTime;
      [440, 554.37, 659.25, 880].forEach(function (freq, i) {
        tone(freq, now + i * 0.1, 0.18, "sawtooth");
      });
    },
    blackout: function () {
      // Power-down glitch: descending pitch bend + a noise burst.
      var c = getContext();
      var now = c.currentTime;
      var osc = c.createOscillator();
      var gain = c.createGain();
      osc.type = "square";
      osc.frequency.setValueAtTime(600, now);
      osc.frequency.exponentialRampToValueAtTime(60, now + 1.2);
      gain.gain.setValueAtTime(0.5, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 1.2);
      osc.connect(gain);
      gain.connect(masterGain);
      osc.start(now);
      osc.stop(now + 1.25);
      track(osc);
      noiseBurst(now, 0.3);
    },
    reveal: function () {
      // Celebration fanfare: bright ascending chord + sustained triad.
      var c = getContext();
      var now = c.currentTime;
      [659.25, 783.99, 987.77, 1318.5].forEach(function (freq, i) {
        tone(freq, now + i * 0.1, 0.3, "triangle");
      });
      [523.25, 659.25, 783.99].forEach(function (freq) {
        tone(freq, now + 0.45, 1.2, "sine");
      });
    },
  };

  function fire(key, label) {
    CUES[key]();
    var log = document.getElementById("last-fired");
    var now = new Date();
    log.textContent = "Last triggered: " + label + " at " + now.toLocaleTimeString();
  }

  function stopAll() {
    activeNodes.forEach(function (node) {
      try {
        node.stop();
      } catch (e) {
        /* already stopped */
      }
    });
    activeNodes = [];
  }

  function init() {
    var buttons = document.querySelectorAll("button[data-cue]");
    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        fire(btn.dataset.cue, btn.dataset.label);
      });
    });

    document.getElementById("stop-all").addEventListener("click", stopAll);

    var volume = document.getElementById("volume");
    volume.addEventListener("input", function () {
      getContext();
      masterGain.gain.value = parseFloat(volume.value);
    });

    document.addEventListener("keydown", function (e) {
      var idx = parseInt(e.key, 10);
      if (idx >= 1 && idx <= buttons.length) {
        buttons[idx - 1].click();
      }
    });
  }

  document.addEventListener("DOMContentLoaded", init);
})();
