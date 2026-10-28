# PDF Hidden Text: The Redacted Exam Paper

**Track:** Forensics & Stego  
**Difficulty:** Easy — 300 → 100 pts (decay 20 solves)  
**Author:** Yesha (Forensics Track Lead)  
**Flag:** `case{redacted_pdf_layer_text_exposed}`

---

## 1. Challenge Overview & Canon Storyline
Before circulating the official exam schedule, Prof. ManMishra Chelaiya prepared the master draft of the OOP 99 mid-sem examination. Before sending the draft to department colleagues, he attempted to redact Section C (containing Question 4 and the confidential bonus rubric) using black boxes in a PDF editor.

However, the redaction was purely cosmetic: a vector rectangle (`48 330 515 90 re f`) and white text (`1 1 1 rg`) were placed into the PDF stream without rasterizing or sanitizing the content stream. When TA Piyush Pelaiya intercepted the file, he discovered that the original text remained fully intact in the underlying document object.

---

## 2. Anti-AI Defensive Principle
- **Occluded Visual Layer vs. Structural Stream:** Visual inspection or screenshot OCR reveals only an opaque black bar over Section C. Standard vision LLMs prompting on document images will report that Section C is redacted.
- **PDF Structural Analysis:** Solving the challenge requires basic command-line file triage (`pdftotext`, `qpdf`, `strings`, or PDF stream parsing), teaching participants the real-world danger of superficial redactions in PDF documents.

---

## 3. Step-by-Step Solution Walkthrough

### Method A: pdftotext CLI One-Liner
```bash
pdftotext files/OOP99_Exam_Paper_REDACTED.pdf - | grep "case{"
```
Output:
```text
LEAKED ANSWER KEY FLAG: case{redacted_pdf_layer_text_exposed}
```

### Method B: Strings Extraction
```bash
strings files/OOP99_Exam_Paper_REDACTED.pdf | grep "case{"
```

### Method C: Highlight & Copy in PDF Viewer
Open `OOP99_Exam_Paper_REDACTED.pdf` in Google Chrome, Mozilla Firefox, Preview, or Adobe Acrobat. Click and drag the mouse cursor across the black rectangle in Section C, press `Ctrl+C` / `Cmd+C`, and paste into a text editor.

### Method D: Automated Python Solver
```bash
uv run python challenges/pdf_hidden_text/solve.py
```
Output:
```text
[*] Solving PDF Hidden Text challenge from: .../OOP99_Exam_Paper_REDACTED.pdf
[+] Recovered flag via direct PDF content stream inspection: case{redacted_pdf_layer_text_exposed}
[SUCCESS] Validated Flag: case{redacted_pdf_layer_text_exposed}
```

---

## 4. Verification Protocol
1. [x] Valid PDF document generated at `files/OOP99_Exam_Paper_REDACTED.pdf`.
2. [x] Opens cleanly in standard PDF readers with visual black redaction bar.
3. [x] Generator (`generate.py`) runs reproducibly with zero external dependencies.
4. [x] Solver (`solve.py`) verifies the flag extraction across multiple methods.
5. [x] Challenge configuration (`challenge.yml`) is valid.
