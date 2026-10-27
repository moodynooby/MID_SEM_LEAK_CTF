#!/usr/bin/env python3
"""
AU Faculty Exam Vault - Web Service
Challenge: Cookie / API: Faculty Exam Vault Inspection
Author: Tanish Shah (@tanishshahh)
IEEE AUSB CTF: Case File: The Mid-Sem Leak
"""

import json
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from http.cookies import SimpleCookie
from urllib.parse import urlparse

HOST = "0.0.0.0"
PORT = 5001

FLAG_TRUE = "case{cookie_role_tamper_faculty_access}"
FLAG_HONEYPOT = "case{faculty_admin_portal_root_auth_2026}"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>AU Faculty Exam Vault | Ahmedabad University</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    :root {{
      --bg: #090d16;
      --card-bg: #121826;
      --border: #1f293d;
      --accent: #00f0ff;
      --warning: #ffb703;
      --danger: #ef476f;
      --text: #e2e8f0;
      --muted: #64748b;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }}
    body {{
      background: radial-gradient(circle at top, #141c2e 0%, var(--bg) 100%);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 20px;
    }}
    .container {{
      max-width: 800px;
      width: 100%;
    }}
    header {{
      text-align: center;
      margin-bottom: 30px;
    }}
    .badge {{
      display: inline-block;
      padding: 4px 12px;
      font-size: 11px;
      letter-spacing: 1px;
      text-transform: uppercase;
      border-radius: 999px;
      background: rgba(0, 240, 255, 0.1);
      color: var(--accent);
      border: 1px solid rgba(0, 240, 255, 0.3);
      margin-bottom: 12px;
    }}
    h1 {{
      font-size: 28px;
      font-weight: 700;
      color: #fff;
      margin-bottom: 8px;
    }}
    .subtitle {{
      color: var(--muted);
      font-size: 14px;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    }}
    .status-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px;
      background: rgba(0,0,0,0.3);
      border-radius: 8px;
      border: 1px solid var(--border);
      margin-bottom: 20px;
      font-size: 13px;
    }}
    .status-item span {{
      color: var(--accent);
      font-weight: 600;
    }}
    .access-denied {{
      border-left: 4px solid var(--warning);
      padding: 16px;
      background: rgba(255, 183, 3, 0.05);
      border-radius: 4px;
      margin-top: 15px;
    }}
    .access-granted {{
      border-left: 4px solid #10b981;
      padding: 16px;
      background: rgba(16, 185, 129, 0.08);
      border-radius: 4px;
      margin-top: 15px;
    }}
    .flag-box {{
      margin-top: 20px;
      padding: 16px;
      background: #06111e;
      border: 1px dashed var(--accent);
      border-radius: 8px;
      text-align: center;
    }}
    .flag-value {{
      font-family: 'Consolas', monospace;
      font-size: 18px;
      color: var(--accent);
      user-select: all;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 15px;
      font-size: 13px;
    }}
    th, td {{
      padding: 10px 12px;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }}
    th {{ color: var(--muted); text-transform: uppercase; font-size: 11px; }}
    footer {{
      margin-top: auto;
      text-align: center;
      font-size: 12px;
      color: var(--muted);
      padding: 20px 0;
    }}
    code {{
      background: #1e293b;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: monospace;
      color: #38bdf8;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="badge">AU Internal Exam Staging Network</div>
      <h1>Faculty Exam Vault v1.4</h1>
      <p class="subtitle">Instructor: Prof. Hasmukh Chelaiya &bull; Dept. of Computer Science & Engineering</p>
    </header>

    <div class="card">
      <div class="status-bar">
        <div class="status-item">Current Role: <span>{role}</span></div>
        <div class="status-item">Access Tier: <span>Level {access_tier}</span></div>
        <div class="status-item">Session Status: <span style="color: {status_color};">{status_text}</span></div>
      </div>

      {content_body}
    </div>
  </div>

  <footer>
    <p>Protected by AU Academic Access Security Gateway. Unauthorized inspection will be audited.</p>
  </footer>

  <script>
    // Internal API endpoints for automated grading clients
    // Draft loader: /api/v1/faculty/drafts/oop99
    // Admin health: /api/v1/admin/secret
    console.log("[DEBUG] Exam Vault client initialized. Session Cookie Active: role=" + (document.cookie || "student"));
  </script>
</body>
</html>
"""

class VaultHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Clean logging
        pass

    def parse_session_cookies(self):
        cookie_header = self.headers.get("Cookie", "")
        cookies = SimpleCookie(cookie_header)
        role = cookies["role"].value if "role" in cookies else None
        access_tier = cookies["access_tier"].value if "access_tier" in cookies else None
        return role, access_tier

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. API Route: Honeyflag Endpoint
        if path == "/api/v1/admin/secret":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {
                "status": "AUTHENTICATED",
                "auth_scope": "emergency_root_access",
                "message": "Faculty admin emergency portal token authorized.",
                "flag": FLAG_HONEYPOT
            }
            self.wfile.write(json.dumps(resp, indent=2).encode("utf-8"))
            return

        # 2. API Route: Legitimate Faculty Draft Endpoint
        if path == "/api/v1/faculty/drafts/oop99":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {
                "course": "OOP 99 (Object Oriented Programming)",
                "instructor": "Prof. Hasmukh Chelaiya",
                "term": "Mid-Semester 2026",
                "draft_status": "EXFILTRATED_BY_TA_PIYUSH",
                "flag": FLAG_TRUE
            }
            self.wfile.write(json.dumps(resp, indent=2).encode("utf-8"))
            return

        # 3. Main Web Page Route
        role, access_tier = self.parse_session_cookies()
        set_default_cookies = False

        if role is None or access_tier is None:
            role = "student"
            access_tier = "1"
            set_default_cookies = True

        is_elevated = (role == "faculty_coordinator" or role == "admin") and (access_tier in ["99", "100", "faculty"])

        if is_elevated:
            status_color = "#10b981"
            status_text = "AUTHORIZED (FACULTY COORDINATOR)"
            content_body = f"""
            <div class="access-granted">
              <h3>&#10003; Identity Verified: Faculty Coordinator Privileges Active</h3>
              <p style="margin-top: 6px; font-size: 14px;">Welcome Prof. Chelaiya. You have full access to confidential mid-semester draft examination papers.</p>
            </div>

            <table>
              <thead>
                <tr>
                  <th>Course ID</th>
                  <th>Course Name</th>
                  <th>Instructor</th>
                  <th>Draft Archive</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><code>OS 101</code></td>
                  <td>Operating Systems Principles</td>
                  <td>Prof. Hasmukh Chelaiya</td>
                  <td><span style="color:#10b981;">Finalized</span></td>
                </tr>
                <tr>
                  <td><code>OOP 99</code></td>
                  <td>Object Oriented Programming Systems</td>
                  <td>Prof. Hasmukh Chelaiya</td>
                  <td><span style="color:#ef476f;">LEAKED DRAFT ARCHIVE</span></td>
                </tr>
              </tbody>
            </table>

            <div class="flag-box">
              <p style="font-size: 13px; color: var(--muted); margin-bottom: 6px;">OOP 99 Mid-Sem Staging Verification Flag:</p>
              <div class="flag-value">{FLAG_TRUE}</div>
            </div>
            """
        else:
            status_color = "#ffb703"
            status_text = "RESTRICTED (STUDENT TIER)"
            content_body = """
            <div class="access-denied">
              <h3>&#9888; Restricted Access: Student Account Detected</h3>
              <p style="margin-top: 6px; font-size: 14px;">
                You are currently accessing the system under <code>role=student</code> (Tier Level 1).
                Draft exam papers for <strong>OS 101</strong> and <strong>OOP 99</strong> are strictly restricted to <code>faculty_coordinator</code> accounts with Access Tier &ge; 99.
              </p>
            </div>

            <table style="opacity: 0.6;">
              <thead>
                <tr>
                  <th>Course ID</th>
                  <th>Course Name</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><code>OS 101</code></td>
                  <td>Operating Systems Principles</td>
                  <td>[RESTRICTED TO FACULTY]</td>
                </tr>
                <tr>
                  <td><code>OOP 99</code></td>
                  <td>Object Oriented Programming</td>
                  <td>[RESTRICTED TO FACULTY]</td>
                </tr>
              </tbody>
            </table>

            <p style="margin-top: 20px; font-size: 13px; color: var(--muted);">
              Notice: If you believe you are receiving this message in error, verify your credentials with AU Department IT.
            </p>
            """

        html = HTML_TEMPLATE.format(
            role=role,
            access_tier=access_tier,
            status_color=status_color,
            status_text=status_text,
            content_body=content_body
        )

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        if set_default_cookies:
            self.send_header("Set-Cookie", "role=student; Path=/; SameSite=Lax")
            self.send_header("Set-Cookie", "access_tier=1; Path=/; SameSite=Lax")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

def run():
    server_address = (HOST, PORT)
    httpd = ThreadingHTTPServer(server_address, VaultHandler)
    print(f"[*] AU Faculty Exam Vault server running on http://{HOST}:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down server.")
        httpd.server_close()

if __name__ == "__main__":
    run()
