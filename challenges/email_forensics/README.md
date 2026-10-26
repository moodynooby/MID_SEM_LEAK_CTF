# Email Forensics: The Angry TA's Leaked Mails
## Challenge Writeup & Author Rationale

- **Author:** Vatsal Pandya (`@VP1107`)
- **Track:** Network & Forensics (Issue #5 / Challenge #24)
- **Category:** Forensics
- **Estimated Difficulty:** Medium (Dynamic initial: 500, decay: 15, minimum: 100)
- **Tester / Solve-Verified By:** Krish Poddar (`@Krish-452`) / Manas Doshi (`@moodynooby`)
- **True Flag:** `case{ta_piyush_angry_leaked_oop99_mail}`
- **Alternative Accepted Flag:** `case{piyush_angry_ta_os101_revenge}`
- **Decoy Honeyflags:**
  - `case{decoy_os101_rubric_not_the_leak}`
  - `case{decoy_spoofed_student_submission_flag}`
  - `case{nice_try_blind_ai_decoy_syllabus}`

---

## 1. Challenge Concept & Lore

In *Case File: The Mid-Sem Leak*, midterm examination week at Ahmedabad University's GICT building is thrown into crisis when the upcoming **OOP 99 (Object Oriented Programming Systems)** examination paper is leaked across campus.

The investigation leads back to **TA Piyush Pelaiya**, an M.Tech / Senior Teaching Assistant in GICT Lab 207. Earlier in the semester, Piyush took (and assisted in) **OS 101 (Operating Systems Principles)** under the strict evaluation of **Prof. Hasmukh Chelaiya**. Prof. Chelaiya deducted 25 marks on Piyush's multithreading lab evaluation due to a mutex lock ordering flaw, bluntly declaring in front of the lab: *"Deadlock avoidance is non-negotiable in OS 101, Mr. Pelaiya."*

Furious and seeking revenge, Piyush discovered Prof. Chelaiya's draft of the upcoming OOP 99 mid-sem examination during a late-night workstation share synchronization. In retaliation, Piyush sent an angry exfiltration email to the student body containing the complete leaked question paper and an explicit confession.

To obscure his identity, Piyush spoofed the `From` header as `"Anonymous Student Council" <student_council_leaks@protonmail.com>`. The campus gateway (`mailgw.ahduni.edu.in`) intercepted the outbound transmission and archived an incident export bundle (`leaked_incident_mail.eml`) containing student inquiries, spoofed tips, and the rogue exfiltration blast.

---

## 2. Anti-AI Defensive Architecture

Standard LLMs struggle with multi-layered MIME structures, nested RFC 822 messages, and conflicting header evidence:

1. **Multi-Threaded Spool & Nested `message/rfc822` Encodings:**
   The artifact is a campus incident export containing 4 nested sub-messages:
   - Decoy 1: Innocent student Sansh Vhah inquiring about OS 101 rubric marks (`10.208.15.44`).
   - Decoy 2: An anonymous student complaint attempting to shift blame to Danas Moshi (`10.207.99.101`).
   - Decoy 3: An official academic circular from the Dean's Office regarding exam security.
   - Genuine Exfiltration Blast: The authentic message sent by Piyush Pelaiya.

2. **Automated Honeyflags & Decoy Attachments:**
   Blind text-scraping or naive regex searches for `case{...}` trigger decoy honeyflags:
   - `case{decoy_os101_rubric_not_the_leak}` in `OS101_Assignment2_Rubric_Decoy.pdf`
   - `case{decoy_spoofed_student_submission_flag}` in `Lab207_Incident_Decoy.pdf`
   - `case{nice_try_blind_ai_decoy_syllabus}` in `Dean_Exam_Security_Protocol.pdf`
   Submitting any of these decoy flags to CTFd results in an incorrect submission penalty.

3. **Header Spoofing vs. Internal Authentication Headers:**
   While the visible `From:` header is spoofed to `student_council_leaks@protonmail.com`, forensic inspection of the authenticated RFC 822 envelope reveals:
   - `X-Campus-Auth-User: piyush.pelaiya`
   - `X-Originating-IP: [10.207.42.19]` (Lab 207 TA subnet)
   - `Reply-To: piyush.pelaiya@ahduni.edu.in`
   - `X-Authenticated-Sender: piyush.pelaiya@ahduni.edu.in`

---

## 3. Walkthrough & Official Solution

### Step 1: Inspect the MIME Structure & Sub-Messages
Open `challenges/email_forensics/files/leaked_incident_mail.eml` using any email client (Thunderbird, Apple Mail), a text editor, or Python:

```bash
# Using Python to parse all nested RFC 822 messages
python -c "
import email, email.policy
with open('files/leaked_incident_mail.eml', 'rb') as f:
    msg = email.message_from_binary_file(f, policy=email.policy.default)
for part in msg.walk():
    if part.get_content_type() == 'message/rfc822':
        sub = part.get_payload(0)
        print('From:', sub['From'])
        print('Subject:', sub['Subject'])
        print('X-Originating-IP:', sub.get('X-Originating-IP'))
        print('X-Campus-Auth-User:', sub.get('X-Campus-Auth-User'))
        print('-'*50)
"
```

### Step 2: Trace the Rogue Sender
Observe that while the subject is `[LEAK] OOP 99 Mid-Sem Question Paper Leaked!! Revenge for OS 101!` and the sender claims to be `Anonymous Student Council`, the internal mail server added:
```http
X-Originating-IP: [10.207.42.19]
X-Campus-Auth-User: piyush.pelaiya
Reply-To: piyush.pelaiya@ahduni.edu.in
```
This confirms that **TA Piyush Pelaiya** authored and transmitted this specific message from IP `10.207.42.19`.

### Step 3: Extract the Leaked Exam Paper Attachment
Extract the base64-encoded attachment `OOP99_MidSem_Exam_LEAKED_CONFIDENTIAL.pdf` from the authenticated message:

```bash
# Extract using ripmime, munpack, or python
python -c "
import email, email.policy
with open('files/leaked_incident_mail.eml', 'rb') as f:
    msg = email.message_from_binary_file(f, policy=email.policy.default)
for part in msg.walk():
    fn = part.get_filename()
    if fn and 'OOP99' in fn:
        with open(fn, 'wb') as out:
            out.write(part.get_payload(decode=True))
        print(f'[+] Extracted: {fn}')
"
```

### Step 4: Recover the Flag
Inspect the extracted PDF and the body text of the authenticated email:
- The confession text in the message body reads:
  ```text
  Confession & Signature Flag:
  case{ta_piyush_angry_leaked_oop99_mail}
  ```
- The footer of the authentic exam paper (`OOP99_MidSem_Exam_LEAKED_CONFIDENTIAL.pdf`) contains:
  ```text
  AUTHENTIC CONFESSION & SIGNATURE FLAG:
  case{ta_piyush_angry_leaked_oop99_mail}
  ```

---

## 4. Hints & Cost Strategy

- **Hint 1 (-25 pts):** "Trace the un-spoofed X-Originating-IP and X-Campus-Auth-User headers in the mail thread to isolate the genuine sender message."
- **Hint 2 (-50 pts):** "Beware of decoy attachments in forwarded student threads. Extract the base64 attachment from the message originating from Piyush's IP (10.207.42.19)."

---

## 5. Solve-Test Verification Log

- **Date Tested:** 26/10/2026
- **Automated Verification:** `uv run python challenges/email_forensics/solve.py` $\rightarrow$ Exit code 0.
- **Estimated Human Solve Time:** 8–15 minutes.
- **Verification Summary:**
  - MIME traversal correctly extracts 4 distinct nested message entities.
  - All 3 decoy honeyflags validated and prevented from triggering false positive solves.
  - Base64 payload cleanly decoded to valid PDF-1.4 binary.
  - Whitespace and case-sensitivity verified for `case{ta_piyush_angry_leaked_oop99_mail}`.
