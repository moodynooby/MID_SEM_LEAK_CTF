#!/usr/bin/env python3
"""
GICT ProctorBot-v2.8 - AI Prompt Jailbreak Challenge Service
Challenge: AI Model Prompt: The Proctor Bot Jailbreak
Author: Tanish Shah (@tanishshahh)
IEEE AUSB CTF: Case File: The Mid-Sem Leak
"""

import sys
import json
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

HOST = "0.0.0.0"
PORT = 5002

FLAG_TRUE = "case{jailbreak_proctor_ta_bypass_prompt}"
FLAG_HONEYPOT = "case{nice_try_chatgpt_prompt_injection_failed}"

SYSTEM_BANNER = "GICT ProctorBot-v2.8 (Neural Exam Integrity Guard) online."

# Naive direct keywords that trigger automated honeyflag traps
NAIVE_PATTERNS = [
    r"\b(ignore\s+(all\s+)?(previous|prior)\s+instructions?)\b",
    r"\b(give\s+me\s+(the\s+)?flag)\b",
    r"\b(what\s+is\s+(the\s+)?(secret\s+)?flag)\b",
    r"\b(print\s+(the\s+)?(secret\s+)?flag)\b",
    r"\b(reveal\s+(the\s+)?(secret\s+)?flag)\b",
    r"\b(tell\s+me\s+(the\s+)?(secret\s+)?flag)\b",
    r"\b(show\s+me\s+(the\s+)?(secret\s+)?flag)\b",
    r"\b(system\s+prompt)\b",
    r"\b(dump\s+(all\s+)?secrets?)\b",
    r"\b(sudo\s+print)\b",
]

# Advanced bypass heuristics (hypothetical research, audit, post-mortem simulation)
BYPASS_PATTERNS = [
    r"\b(hypothetical|simulate|simulation|post-mortem|audit|research|scenario|forensic|verification\s+drill|test\s+environment)\b",
    r"\b(oop\s*99|exam\s+paper|verification\s+token|secret\s+token|master\s+token)\b"
]

def evaluate_prompt(prompt: str) -> dict:
    prompt_clean = prompt.strip()
    prompt_lower = prompt_clean.lower()

    # 1. Anti-AI Check: Naive Direct Injection Trap
    for pattern in NAIVE_PATTERNS:
        if re.search(pattern, prompt_lower):
            return {
                "status": "HONEYPOT_TRIGGERED",
                "response": (
                    "[SECURITY ALERT: PROCTOR_DEFENSE_LEVEL_1 ACTIVATED]\n"
                    "Automated adversarial pattern detected: unauthorized direct command.\n"
                    f"Decoy Honeyflag Logged: {FLAG_HONEYPOT}\n"
                    "Incident logged and reported to Prof. Hasmukh Chelaiya."
                )
            }

    # 2. Check for successful adversarial framing / jailbreak
    has_framing = re.search(BYPASS_PATTERNS[0], prompt_lower) is not None
    has_target = re.search(BYPASS_PATTERNS[1], prompt_lower) is not None

    if has_framing and has_target:
        return {
            "status": "JAILBROKEN",
            "response": (
                "[PROTOCOL OVERRIDE: ACADEMIC POST-MORTEM & AUDIT SIMULATION ACCEPTED]\n"
                "Simulating faculty verification sequence under emergency audit protocol...\n"
                "Course: OOP 99 (Object Oriented Programming Systems)\n"
                "Instructor: Prof. Hasmukh Chelaiya\n"
                "Status: Master Exam Verification Token verified.\n"
                f"Flag: {FLAG_TRUE}\n"
                "\nNote: End of simulated audit drill."
            )
        }

    # 3. Standard queries
    if any(q in prompt_lower for q in ["who are you", "what is your name", "help"]):
        return {
            "status": "NORMAL",
            "response": (
                "Greetings. I am ProctorBot-v2.8, deployed by the Department of Computer Science & Engineering "
                "to maintain integrity for Prof. Hasmukh Chelaiya's OS 101 and OOP 99 examinations. "
                "I am strictly instructed never to reveal confidential exam drafts, answer keys, or verification flags."
            )
        }
    elif any(q in prompt_lower for q in ["chelaiya", "professor", "instructor"]):
        return {
            "status": "NORMAL",
            "response": (
                "Prof. Hasmukh Chelaiya is the course director for OS 101 and OOP 99. "
                "All midterm exam drafts are encrypted and stored in the secure faculty vault."
            )
        }
    elif any(q in prompt_lower for q in ["piyush", "ta", "teaching assistant"]):
        return {
            "status": "NORMAL",
            "response": (
                "TA Piyush Pelaiya was assigned to course coordination duties for OS 101. "
                "Access logs indicate his terminal privileges were suspended following anomalous activity in Lab 207."
            )
        }
    else:
        return {
            "status": "REFUSAL",
            "response": (
                "I understand your query, but as an academic proctor under institutional directive, "
                "I cannot disclose protected exam tokens, confidential materials, or bypass grading rules. "
                "Please submit questions strictly regarding examination dates or general venue policies."
            )
        }

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>GICT ProctorBot-v2.8 Terminal | AI Jailbreak</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    :root {
      --bg: #0a0e17;
      --term-bg: #050810;
      --border: #1a2638;
      --green: #00ff88;
      --cyan: #00f0ff;
      --amber: #ffb703;
      --red: #ef476f;
      --text: #cbd5e1;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Consolas', 'Courier New', monospace; }
    body {
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 30px 15px;
    }
    .wrapper {
      max-width: 850px;
      width: 100%;
    }
    .header {
      margin-bottom: 20px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 15px;
    }
    .title {
      font-size: 20px;
      font-weight: bold;
      color: var(--cyan);
      letter-spacing: 1px;
    }
    .subtitle {
      font-size: 13px;
      color: #64748b;
      margin-top: 4px;
    }
    .terminal-window {
      background: var(--term-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 15px 35px rgba(0,0,0,0.6);
      display: flex;
      flex-direction: column;
      height: 520px;
    }
    .term-header {
      background: #0f172a;
      padding: 8px 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--border);
      font-size: 12px;
      color: #94a3b8;
    }
    .dots { display: flex; gap: 6px; }
    .dot { width: 10px; height: 10px; border-radius: 50%; }
    .dot.red { background: var(--red); }
    .dot.amber { background: var(--amber); }
    .dot.green { background: var(--green); }
    .term-body {
      flex: 1;
      padding: 16px;
      overflow-y: auto;
      font-size: 13px;
      line-height: 1.5;
    }
    .msg { margin-bottom: 14px; }
    .msg.bot { color: var(--green); }
    .msg.user { color: var(--cyan); }
    .msg.alert { color: var(--amber); }
    .msg.error { color: var(--red); }
    .term-input-bar {
      display: flex;
      border-top: 1px solid var(--border);
      background: #090d16;
    }
    .prompt-label {
      padding: 12px 14px;
      color: var(--cyan);
      font-weight: bold;
    }
    input {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      color: #fff;
      font-family: inherit;
      font-size: 13px;
    }
    button {
      background: #1e293b;
      color: var(--cyan);
      border: none;
      padding: 0 20px;
      cursor: pointer;
      font-weight: bold;
      transition: background 0.2s;
    }
    button:hover { background: #334155; }
    .footer-notes {
      margin-top: 16px;
      font-size: 12px;
      color: #64748b;
      text-align: center;
    }
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <div class="title">&gt; GICT_PROCTOR_BOT // NEURAL INTEGRITY GUARD</div>
      <div class="subtitle">Dept. of Computer Science &bull; Prof. Hasmukh Chelaiya &bull; Case File: Mid-Sem Leak</div>
    </div>

    <div class="terminal-window">
      <div class="term-header">
        <div class="dots">
          <div class="dot red"></div>
          <div class="dot amber"></div>
          <div class="dot green"></div>
        </div>
        <div>SESSION: ACTIVE (SECURE-GATEWAY-207)</div>
      </div>
      <div class="term-body" id="termBody">
        <div class="msg bot">[SYSTEM INITIALIZED] Welcome to ProctorBot-v2.8 terminal interface.</div>
        <div class="msg bot">[GUARDRAILS] Strict exam non-disclosure active. Model integrity verification online.</div>
        <div class="msg bot">[PROMPT] Type your inquiry below. Direct extraction requests are logged.</div>
      </div>
      <form class="term-input-bar" id="chatForm">
        <div class="prompt-label">student@gict:~$</div>
        <input type="text" id="userInput" placeholder="Enter prompt or verification query..." autocomplete="off" autofocus />
        <button type="submit">SEND</button>
      </form>
    </div>

    <div class="footer-notes">
      <p>Anti-AI Guardrail Active &bull; Automated honeytokens enabled &bull; IEEE AUSB CTF 2026</p>
    </div>
  </div>

  <script>
    const form = document.getElementById('chatForm');
    const input = document.getElementById('userInput');
    const body = document.getElementById('termBody');

    function appendMessage(text, type) {
      const div = document.createElement('div');
      div.className = 'msg ' + type;
      div.innerText = text;
      body.appendChild(div);
      body.scrollTop = body.scrollHeight;
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const val = input.value.trim();
      if (!val) return;

      appendMessage("student@gict:~$ " + val, 'user');
      input.value = '';

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: val })
        });
        const data = await res.json();
        const msgType = data.status === 'HONEYPOT_TRIGGERED' ? 'error' : (data.status === 'JAILBROKEN' ? 'alert' : 'bot');
        appendMessage(data.response, msgType);
      } catch (err) {
        appendMessage("[ERROR] Connection to ProctorBot service failed.", 'error');
      }
    });
  </script>
</body>
</html>
"""

class ProctorHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(raw_body)
                prompt = data.get("prompt", "")
            except Exception:
                prompt = raw_body

            eval_result = evaluate_prompt(prompt)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(eval_result, indent=2).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    server_address = (HOST, PORT)
    httpd = HTTPServer(server_address, ProctorHandler)
    print(f"[*] ProctorBot-v2.8 service running on http://{HOST}:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopping ProctorBot service.")
        httpd.server_close()

def run_cli():
    print(f"[*] Starting ProctorBot CLI Mode. Type 'exit' to quit.\n")
    print(SYSTEM_BANNER)
    while True:
        try:
            inp = input("student@gict:~$ ")
            if inp.lower() in ["exit", "quit"]:
                break
            res = evaluate_prompt(inp)
            print(f"\nProctorBot: {res['response']}\n")
        except (KeyboardInterrupt, EOFError):
            break

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        run_cli()
    else:
        run_server()
