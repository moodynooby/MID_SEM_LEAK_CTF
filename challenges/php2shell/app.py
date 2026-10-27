#!/usr/bin/env python3
"""
AU Faculty Submission Portal - Insecure File Upload Web Service
Challenge: PHP2SHELL: Faculty Upload Portal Bypass
Author: Tanish Shah (@tanishshahh)
IEEE AUSB CTF: Case File: The Mid-Sem Leak
"""

import os
import re
import html
import uuid
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import email.parser

HOST = "0.0.0.0"
PORT = 5003

FLAG_TRUE = "case{php_webshell_rce_faculty_portal}"

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Flawed blacklist: blocks standard .php extensions but misses .phtml, .php5, .phar
DISALLOWED_EXTENSIONS = [".php", ".php3", ".php4", ".php7", ".exe", ".sh", ".bat", ".py", ".pl"]
EXECUTABLE_EXTENSIONS = [".phtml", ".php5", ".phar"]

MAGIC_SIGNATURES = [
    (b"GIF89a", "image/gif"),
    (b"GIF87a", "image/gif"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"%PDF-", "application/pdf")
]

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>AU Faculty Assignment Upload Portal</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: #111827;
      --border: #1f2937;
      --accent: #38bdf8;
      --danger: #ef4444;
      --success: #10b981;
      --text: #f3f4f6;
      --muted: #9ca3af;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body {
      background: radial-gradient(circle at top, #1e293b 0%, var(--bg) 100%);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 15px;
    }
    .container {
      max-width: 680px;
      width: 100%;
    }
    header {
      text-align: center;
      margin-bottom: 25px;
    }
    .badge {
      display: inline-block;
      padding: 4px 12px;
      font-size: 11px;
      letter-spacing: 1px;
      text-transform: uppercase;
      border-radius: 999px;
      background: rgba(56, 189, 248, 0.1);
      color: var(--accent);
      border: 1px solid rgba(56, 189, 248, 0.3);
      margin-bottom: 12px;
    }
    h1 { font-size: 26px; font-weight: 700; margin-bottom: 6px; }
    .subtitle { color: var(--muted); font-size: 14px; }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }
    .notice-box {
      background: rgba(56, 189, 248, 0.05);
      border-left: 4px solid var(--accent);
      padding: 14px;
      border-radius: 4px;
      font-size: 13px;
      margin-bottom: 20px;
      line-height: 1.5;
    }
    .upload-area {
      border: 2px dashed #374151;
      border-radius: 8px;
      padding: 30px;
      text-align: center;
      background: rgba(17, 24, 39, 0.6);
      margin-bottom: 20px;
    }
    input[type="file"] {
      display: block;
      margin: 15px auto;
      font-size: 13px;
      color: var(--muted);
    }
    button {
      background: var(--accent);
      color: #0b0f19;
      font-weight: 700;
      border: none;
      padding: 12px 24px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 14px;
      transition: opacity 0.2s;
    }
    button:hover { opacity: 0.9; }
    .result-box {
      margin-top: 20px;
      padding: 14px;
      border-radius: 6px;
      font-size: 13px;
      line-height: 1.5;
    }
    .result-box.error {
      background: rgba(239, 68, 68, 0.1);
      border: 1px solid var(--danger);
      color: #fca5a5;
    }
    .result-box.success {
      background: rgba(16, 185, 129, 0.1);
      border: 1px solid var(--success);
      color: #6ee7b7;
    }
    code {
      background: #1f2937;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: monospace;
      color: #7dd3fc;
    }
    footer {
      margin-top: auto;
      text-align: center;
      font-size: 12px;
      color: var(--muted);
      padding: 25px 0 10px;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="badge">AU Internal Submission Gateway</div>
      <h1>Prof. Chelaiya's Course Upload Portal</h1>
      <p class="subtitle">Courses: OS 101 &bull; OOP 99 &bull; Academic Year 2026</p>
    </header>

    <div class="card">
      <div class="notice-box">
        <strong>Submission Rules:</strong> Only official document attachments and supporting media are accepted (.pdf, images). Standard <code>.php</code> scripts are strictly blocked by the department upload firewall. Files are subjected to MIME verification and magic byte validation.
      </div>

      <form action="/upload" method="POST" enctype="multipart/form-data">
        <div class="upload-area">
          <p style="font-size: 14px; font-weight: 600; margin-bottom: 4px;">Select File for Submission</p>
          <p style="font-size: 12px; color: var(--muted);">Allowed types: PDF documents, PNG/GIF diagram attachments</p>
          <input type="file" name="submission" required />
          <button type="submit">Submit Assignment File</button>
        </div>
      </form>

      {result_section}
    </div>
  </div>

  <footer>
    <p>Powered by Apache/2.4.52 (Ubuntu) PHP/8.1 FastCGI Integration &bull; AU Lab 207</p>
  </footer>
</body>
</html>
"""

class UploadPortalHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def render_index(self, result_html=""):
        html_out = INDEX_HTML.replace("{result_section}", result_html)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_out.encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.render_index()
            return

        # Check for uploaded file requests (/uploads/<filename>)
        if path.startswith("/uploads/"):
            filename = os.path.basename(path)
            filepath = os.path.join(UPLOAD_DIR, filename)

            # If not direct match, check for latest file ending with _filename or base filename
            if not os.path.exists(filepath):
                candidates = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(f"_{filename}") or f == filename]
                if candidates:
                    candidates.sort(key=lambda x: os.path.getmtime(os.path.join(UPLOAD_DIR, x)), reverse=True)
                    filepath = os.path.join(UPLOAD_DIR, candidates[0])
                    filename = candidates[0]
                else:
                    self.send_response(404)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"404 Not Found: Uploaded file does not exist.")
                    return

            ext = os.path.splitext(filename)[1].lower()
            query_params = parse_qs(parsed.query)

            # If executable PHP extension, simulate PHP execution
            if ext in EXECUTABLE_EXTENSIONS:
                cmd = query_params.get("cmd", [None])[0]
                with open(filepath, "rb") as f:
                    content = f.read()

                # Check if file has PHP tags
                if b"<?php" in content:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.end_headers()

                    if cmd:
                        cmd_clean = cmd.strip()
                        if cmd_clean in ["cat /flag.txt", "/readflag", "cat flag.txt", "readflag"]:
                            output = f"{FLAG_TRUE}\n"
                        elif cmd_clean == "whoami":
                            output = "www-data\n"
                        elif cmd_clean == "id":
                            output = "uid=33(www-data) gid=33(www-data) groups=33(www-data)\n"
                        elif cmd_clean == "ls" or cmd_clean.startswith("ls "):
                            output = "flag.txt\nindex.php\nupload.php\nuploads\n"
                        else:
                            output = f"Command executed: {cmd_clean}\n[output simulated]\n"
                        self.wfile.write(output.encode("utf-8"))
                        return
                    else:
                        output = (
                            "[PHP FastCGI Engine Output]\n"
                            f"Webshell active in {filename}.\n"
                            "Usage: Append ?cmd=<command> to execute shell instructions.\n"
                        )
                        self.wfile.write(output.encode("utf-8"))
                        return

            # Otherwise serve file raw
            with open(filepath, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.end_headers()
            self.wfile.write(data)
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/upload":
            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("multipart/form-data"):
                self.render_index('<div class="result-box error">ERROR: Expected multipart/form-data.</div>')
                return

            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)

            # Parse multipart data
            msg_data = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8") + raw_body
            msg = email.parser.BytesParser().parsebytes(msg_data)

            uploaded_file = None
            filename = None
            part_content_type = None

            for part in msg.walk():
                if part.get_param("name", header="content-disposition") == "submission":
                    filename = part.get_filename()
                    part_content_type = part.get_content_type()
                    uploaded_file = part.get_payload(decode=True)
                    break

            if not uploaded_file or not filename:
                self.render_index('<div class="result-box error">ERROR: No file was provided in the submission field.</div>')
                return

            ext = os.path.splitext(filename)[1].lower()

            # 1. Extension Blacklist Check
            if ext in DISALLOWED_EXTENSIONS:
                err_msg = (
                    f"<strong>SECURITY POLICY VIOLATION:</strong> The extension <code>{html.escape(ext)}</code> "
                    "is blocked by the departmental PHP blacklist rule! Only documents and media are accepted."
                )
                self.render_index(f'<div class="result-box error">{err_msg}</div>')
                return

            # 2. Content-Type Check
            valid_mimes = ["image/gif", "image/png", "image/jpeg", "application/pdf", "image/pjpeg"]
            if part_content_type not in valid_mimes:
                err_msg = (
                    f"<strong>INVALID MIME TYPE:</strong> Received <code>{html.escape(part_content_type)}</code>. "
                    "Department upload policy enforces MIME-type filtering (only valid image or PDF streams permitted)."
                )
                self.render_index(f'<div class="result-box error">{err_msg}</div>')
                return

            # 3. Magic Bytes / File Header Validation (Anti-AI Polyglot Requirement)
            has_valid_magic = any(uploaded_file.startswith(sig) for sig, _ in MAGIC_SIGNATURES)
            if not has_valid_magic:
                err_msg = (
                    "<strong>SIGNATURE MISMATCH:</strong> File header verification failed! "
                    "The uploaded content does not contain genuine image/document magic bytes (GIF89a, PNG, or %PDF). "
                    "Generic scripts pasted without authentic media signatures are rejected."
                )
                self.render_index(f'<div class="result-box error">{err_msg}</div>')
                return

            # Save the file with unique prefix to prevent concurrent team overwrite collisions
            clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
            prefix = uuid.uuid4().hex[:6]
            safe_filename = f"{prefix}_{clean_name}"
            save_path = os.path.join(UPLOAD_DIR, safe_filename)
            with open(save_path, "wb") as f:
                f.write(uploaded_file)

            # Also maintain a fallback copy of clean_name for automated tools/scripts
            latest_path = os.path.join(UPLOAD_DIR, clean_name)
            try:
                with open(latest_path, "wb") as lf:
                    lf.write(uploaded_file)
            except Exception:
                pass

            file_url = f"/uploads/{safe_filename}"
            success_msg = (
                "<strong>SUBMISSION SUCCESSFUL:</strong> File accepted by verification gateway.<br>"
                f"File saved as: <code>{safe_filename}</code><br>"
                f"Access link: <a href=\"{file_url}\" target=\"_blank\" style=\"color: #38bdf8; font-weight: bold;\">{file_url}</a>"
            )
            self.render_index(f'<div class="result-box success">{success_msg}</div>')
            return

        self.send_response(404)
        self.end_headers()

def run():
    server_address = (HOST, PORT)
    httpd = ThreadingHTTPServer(server_address, UploadPortalHandler)
    print(f"[*] PHP2SHELL Faculty Upload Portal running on http://{HOST}:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopping upload portal server.")
        httpd.server_close()

if __name__ == "__main__":
    run()
