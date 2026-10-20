# Docket #102: The Fictional Exam Portal Breach

- **Category:** Web / Forensics (Dual Route)
- **Flag:** `case{sql1_byp4ss_found_in_syslog}`
- **Story Arc:** Act II — Discovering the breach vector into the internal portal.

## Concept & Solution
Teams can choose their comfort level:
- **Route A (Forensics / Log reading):** Grep for `admin' OR 1=1` or urlencoded payloads `%27%20OR%201=1` inside `portal_access.log`. The resulting URL parameter contains the base64 flag.
- **Route B (Web Inspection):** Reviewing the Python Flask login route where insecure string formatting directly executes SQL queries without parameterization.
