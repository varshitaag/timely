# timely
# Date Extractor

A Python script that extracts dates from various file types including images, PDFs, emails, and text files.

## Features

- **Image Processing**: Extracts dates from images using OCR (JPG, PNG, GIF, BMP, TIFF)
- **PDF Processing**: Extracts dates from PDF documents
- **Email Processing**: Extracts dates from email files (.eml, .msg)
- **Text Processing**: Extracts dates from text files and forwarded messages
- **Multiple Date Formats**: Recognizes various date formats (MM/DD/YYYY, YYYY-MM-DD, Month DD YYYY, etc.)
- **Batch Processing**: Can process multiple files or entire directories at once

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Tesseract OCR** (required for image processing):
   
   - **Ubuntu/Debian:**
     ```bash
     sudo apt-get install tesseract-ocr
     ```
   
   - **macOS:**
     ```bash
     brew install tesseract
     ```
   
   - **Windows:**
     Download installer from: https://github.com/UB-Mannheim/tesseract/wiki

## Usage

### Basic Usage

Process a single file:
```bash
python date_extractor.py document.pdf
```

Process multiple files:
```bash
python date_extractor.py image.jpg email.eml report.pdf
```

Process all files in a directory:
```bash
python date_extractor.py ./my_documents/
```

### Output

The script creates an `extracted_dates.txt` file containing all found dates organized by source file.

Example output:
```
Date Extraction Results
Generated: 2024-02-11 10:30:00
================================================================================

File: document.pdf
--------------------------------------------------------------------------------
  • 2024-01-15 (page 1)
  • January 20, 2024 (page 1)
  • 03/15/2024 (page 2)

File: email.eml
--------------------------------------------------------------------------------
  • Email Date: Mon, 5 Feb 2024 14:23:10 -0800
  • Body: 2024-02-10 (meeting scheduled)
```

### Supported File Types

- **Images**: .jpg, .jpeg, .png, .gif, .bmp, .tiff
- **PDFs**: .pdf
- **Emails**: .eml, .msg
- **Text**: .txt, .md, or any text-based file

### Supported Date Formats

The script recognizes various date formats including:
- MM/DD/YYYY or DD/MM/YYYY (e.g., 02/11/2024)
- YYYY-MM-DD (e.g., 2024-02-11)
- Month DD, YYYY (e.g., February 11, 2024)
- DD Month YYYY (e.g., 11 February 2024)
- And many more natural language formats

## Notes

- The script attempts to install gracefully - if OCR or PDF libraries aren't available, it will skip those file types
- For best results with images, ensure they have good contrast and readable text
- Email date extraction includes dates from headers, subject, and body
- When processing directories, the script recursively processes all supported files

## Troubleshooting

**"pytesseract not found" error:**
- Make sure Tesseract OCR is installed on your system (not just the Python package)

**Poor OCR results:**
- Ensure images are clear and high-resolution
- Pre-process images to improve contrast if needed

**No dates found:**
- Check that the date format is recognizable
- The file might not contain any dates
- Try viewing the extracted text to ensure it's readable

# timely — Date Extractor

A Python tool that extracts dates from images, PDFs, emails, and text files.

---

## File Structure

| File | Purpose |
|---|---|
| `dateExtractor.py` | Core extraction logic — the `DateExtractor` class |
| `main.py` | Command-line interface — reads arguments and calls the extractor |

---

## Installation

```bash
pip install pillow pytesseract PyPDF2 python-dateutil
```

For image OCR, also install **Tesseract** on your system:
- **Windows** → https://github.com/UB-Mannheim/tesseract/wiki
- **macOS** → `brew install tesseract`
- **Ubuntu** → `sudo apt-get install tesseract-ocr`

---

## Usage

```bash
python main.py document.pdf
python main.py image.jpg email.eml report.pdf
python main.py ./documents_folder/
```

Results are saved to `extracted_dates.txt` in the current directory.

---

## Code Comment Reference

Every important line in both files is marked with a `[number]`.
This section explains what each numbered comment means.

---

### `dateExtractor.py` — Imports & Setup

| # | Line | Explanation |
|---|---|---|
| 1 | `import re` | Loads Python's regex engine. Used to search for date patterns like `01/15/2024` inside strings. |
| 2 | `import os` | Provides access to environment variables (`os.environ`) and file checks (`os.path.exists`). |
| 3 | `from datetime import datetime` | Used in `save_results()` to stamp the output file with the current date and time. |
| 4 | `from pathlib import Path` | Replaces manual string slicing for file paths. Works identically on Windows, Mac, and Linux. |
| 5 | `import email` | Python's built-in email parser. Converts raw `.eml` binary bytes into a structured object with headers and body. |
| 6 | `from email import policy` | Controls how the email is decoded. `policy.default` uses the modern, standards-compliant decoder. |
| 7 | *(removed line)* | `from tkinter import Image` was a leftover error in the original code. Tkinter's `Image` is unrelated to PIL/Pillow and would cause a crash. It is removed here. |
| 8 | `try: from PIL import Image ...` | Wraps optional imports in `try/except` so the script still runs even if these libraries are not installed. |
| 9 | `from PIL import Image` | Pillow's Image class. Opens image files (JPG, PNG, BMP, TIFF) so their contents can be passed to OCR. |
| 10 | `import pytesseract` | Python wrapper for Tesseract OCR. Sends the opened image to Tesseract and receives the extracted text back. |
| 11 | `import sys` | Imported inside the `try` block to check `sys.platform` for the OS detection below. |
| 12 | `if sys.platform == 'win32'` | Detects if the script is running on Windows. Tesseract's path setup is only needed on Windows. |
| 13 | `tesseract_path = r'C:\Users\Varsh\...'` | Hardcoded path to the `tesseract.exe` binary. Change this to match your own Tesseract installation path. |
| 14 | `pytesseract.pytesseract.tesseract_cmd = tesseract_path` | Tells pytesseract exactly where the Tesseract executable lives, instead of relying on the system PATH. |
| 15 | `os.environ['TESSDATA_PREFIX'] = r'...\tessdata'` | Sets an environment variable pointing to Tesseract's language data folder (e.g. `eng.traineddata`). Without this, OCR fails with a "language not found" error. |
| 16 | `OCR_AVAILABLE = True` | Flag set to `True` when all OCR imports succeed. Checked in `extract_from_image()` before running OCR. |
| 17 | `OCR_AVAILABLE = False` | Set in the `except` block if Pillow or pytesseract is missing. Image files will be skipped with a warning. |
| 18 | `try: import PyPDF2 ...` | Optional import block for PDF support. A missing PyPDF2 will not crash the whole script. |
| 19 | `import PyPDF2` | Library that opens PDF files and extracts selectable text from each page. Does not work on scanned/image-only PDFs. |
| 20 | `PDF_AVAILABLE = True` | Flag confirming PyPDF2 loaded successfully. |
| 21 | `PDF_AVAILABLE = False` | Set if PyPDF2 is not installed. PDF files will be skipped. |
| 22 | `try: from dateutil import parser ...` | Optional import block for dateutil. Regex alone still works if dateutil is missing. |
| 23 | `from dateutil import parser as date_parser` | dateutil parses complex natural-language dates like `"5th of March, 2024"` that regex might miss. |
| 24 | `DATEUTIL_AVAILABLE = True` | Flag confirming dateutil loaded successfully. |
| 25 | `DATEUTIL_AVAILABLE = False` | Set if dateutil is not installed. Only regex patterns will be used for date detection. |

---

### `dateExtractor.py` — The `DateExtractor` Class

| # | Line | Explanation |
|---|---|---|
| 26 | `class DateExtractor:` | Defines a class that bundles all extraction logic. One instance gives access to all methods and shared state. |
| 27 | `def __init__(self, output_file=...)` | Constructor. Runs automatically when `DateExtractor()` is called. Accepts an optional output filename. |
| 28 | `self.output_file = output_file` | Saves the output filename inside the object so `save_results()` can access it without being passed it again. |
| 29 | `self.extracted_dates = []` | Empty list that accumulates results. Each entry is a dict: `{'file': '...', 'dates': [...]}`. |
| 30 | `self.date_patterns = [...]` | List of 6 regex patterns. Each covers a different date format. All are applied to every piece of text processed. |
| 31 | `r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'` | Matches numeric dates: `01/15/2024`, `15-01-24`. `\b` = word boundary; `[/-]` = slash or dash separator. |
| 32 | `r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b'` | Matches ISO-style year-first dates: `2024-01-15`, `2024/01/15`. |
| 33 | `r'\b(?:Jan\|Feb\|...) \d{1,2},? \d{4}\b'` | Matches abbreviated month names: `Jan 15, 2024`. `[a-z]*` also allows full spellings like `January`. |
| 34 | `r'\b\d{1,2} (?:Jan\|Feb\|...) \d{4}\b'` | Matches day-first formats: `15 Jan 2024`, common in European/Indian conventions. |
| 35 | `r'\b(?:January\|February\|...) \d{1,2},? \d{4}\b'` | Matches fully-spelled month names: `January 15, 2024`, `March 5 2024`. |
| 36 | `r'\b\d{1,2}(?:st\|nd\|rd\|th)? (?:of )?...\b'` | Matches ordinal dates: `1st of January 2024`, `3rd March 2024`. |

---

### `dateExtractor.py` — `extract_dates_from_text()`

| # | Line | Explanation |
|---|---|---|
| 37 | `dates = []` | Fresh empty list for this call. Collects every date string found in the text passed to this method. |
| 38 | `for pattern in self.date_patterns:` | Loops through all 6 regex patterns. Each is applied to the full text independently. |
| 39 | `re.findall(pattern, text, re.IGNORECASE)` | Returns a list of all non-overlapping matches. `re.IGNORECASE` means `JAN`, `Jan`, and `jan` all match. |
| 40 | `dates.extend(matches)` | Adds every match individually to the list. Unlike `append`, `extend` doesn't create a nested list. |
| 41 | `if DATEUTIL_AVAILABLE:` | Only enters the dateutil block if that library was successfully imported. |
| 42 | `words = text.split()` | Splits the full text into individual words. e.g. `"Meet Jan 5"` → `["Meet", "Jan", "5"]`. |
| 43 | `for i in range(len(words)):` | Iterates over every word index as a possible start of a date phrase. |
| 44 | `for length in range(2, min(5, ...)):` | Tries building phrases of 2, 3, and 4 words. Skips single words to avoid false positives like standalone `"May"`. |
| 45 | `phrase = ' '.join(words[i:i+length])` | Joins a slice of consecutive words back with spaces to form a candidate date phrase. |
| 46 | `date_parser.parse(phrase, fuzzy=False)` | Asks dateutil to parse the phrase as a date. `fuzzy=False` requires the whole phrase to look like a date — no partial matches. |
| 47 | `parsed_date.strftime('%Y-%m-%d')` | Converts the successfully parsed date to the standard `YYYY-MM-DD` format for consistent output. |
| 48 | `already_found = [d.split()[0] ...]` | Extracts just the `YYYY-MM-DD` portion from entries already in `dates` to avoid writing duplicates. |
| 49 | `dates.append(f"{date_str} ({phrase})")` | Saves the normalised date alongside the original phrase in brackets so users can trace where it came from. |
| 50 | `except (ValueError, OverflowError):` | `ValueError` = dateutil couldn't parse it. `OverflowError` = extreme numeric value. Both are silently skipped. |
| 51 | `return dates` | Returns the complete list of all date strings found in this piece of text. |

---

### `dateExtractor.py` — `extract_from_image()`

| # | Line | Explanation |
|---|---|---|
| 52 | `if not OCR_AVAILABLE:` | Checks the import flag. Returns an empty list immediately if OCR libraries are missing — no crash. |
| 53 | `import subprocess` | Lazy import — only loaded when this function is called. Lets Python run Tesseract as an external shell command. |
| 54 | `import tempfile` | Creates a disposable temporary file on disk to capture the text output from Tesseract. |
| 55 | `tesseract_cmd = r'C:\Users\Varsh\...'` | Path to the Tesseract binary. The `r` prefix makes it a raw string so `\` is treated as a literal backslash. |
| 56 | `image_path_str = str(image_path)` | Converts the `Path` object to a plain string because `subprocess` requires string arguments, not Path objects. |
| 57 | `output_file = tmp.name` | Captures the auto-generated path of the temporary file. Tesseract will write its OCR output here. |
| 58 | `env = os.environ.copy()` | Copies current environment variables into a new dict so we can modify it without affecting the global process environment. |
| 59 | `env['TESSDATA_PREFIX'] = r'...'` | Overrides the language data path in the copied env dict. Passed to the subprocess so Tesseract can locate language files. |
| 60 | `cmd = [tesseract_cmd, image_path_str, output_file.replace('.txt', '')]` | Builds the Tesseract command as a list. Tesseract appends `.txt` automatically, so we strip it from the base path. |
| 61 | `subprocess.run(cmd, env=env, capture_output=True, text=True)` | Runs Tesseract. `capture_output=True` prevents console spam. `text=True` returns stdout/stderr as strings. |
| 62 | `if os.path.exists(output_file):` | Confirms Tesseract actually produced an output file before attempting to read it. |
| 63 | `text = f.read()` | Reads all OCR-extracted text from Tesseract's output file into a single string. |
| 64 | `os.remove(output_file)` | Deletes the temporary file immediately after reading. Keeps the filesystem clean. |
| 65 | `return self.extract_dates_from_text(text)` | Passes the OCR-extracted text to the date-finding method and returns its results. |

---

### `dateExtractor.py` — `extract_from_pdf()`

| # | Line | Explanation |
|---|---|---|
| 66 | `if not PDF_AVAILABLE:` | Checks the import flag. Returns early with a warning if PyPDF2 is not installed. |
| 67 | `open(pdf_path, 'rb')` | Opens the PDF in **binary read** mode. PDFs are binary files — opening in text mode would corrupt the data. |
| 68 | `PyPDF2.PdfReader(file)` | Creates a reader object from the file handle. Provides access to page count, metadata, and individual pages. |
| 69 | `enumerate(pdf_reader.pages)` | `enumerate` yields `(index, page_object)` pairs, giving us the page number alongside the page content. |
| 70 | `page.extract_text()` | Extracts all selectable text from the current page as a string. Returns empty string for scanned image pages. |
| 71 | `self.extract_dates_from_text(text)` | Runs all regex and dateutil checks on this page's text. |
| 72 | `f"{d} (page {page_num + 1})"` | Tags each date with its source page. `+ 1` converts from 0-based internal index to human-readable page numbering. |

---

### `dateExtractor.py` — `extract_from_email()`

| # | Line | Explanation |
|---|---|---|
| 73 | `open(email_path, 'rb')` | Opens the `.eml` file in binary mode. Raw email files contain encoded bytes, not plain text. |
| 74 | `email.message_from_binary_file(f, policy=policy.default)` | Parses binary email bytes into a structured Python object with accessible headers (`msg['Date']`, `msg['Subject']`) and body. |
| 75 | `if msg['Date']:` | Checks for a `Date:` header before accessing it. Malformed or draft emails may not have one. |
| 76 | `dates.append(f"Email Date: {msg['Date']}")` | Adds the send timestamp. It's already a formatted date string from the email server (e.g. `Mon, 5 Feb 2024 14:23:10 -0800`). |
| 77 | `if msg['Subject']:` | Checks the subject exists before searching it for dates. |
| 78 | `self.extract_dates_from_text(msg['Subject'])` | Searches the subject line. Meeting invites often embed dates directly in the subject. |
| 79 | `[f"Subject: {d}" for d in subject_dates]` | Labels each found date so the output file shows it came from the subject line. |
| 80 | `body = ""` | Initialises an empty accumulator for the email body text. |
| 81 | `if msg.is_multipart():` | Detects whether the email has multiple sections (plain text + HTML + attachments). |
| 82 | `for part in msg.walk():` | Walks through every nested part and sub-part of a multipart email. |
| 83 | `if part.get_content_type() == "text/plain":` | Selects only the plain text sections, skipping HTML (`text/html`) and attachments. |
| 84 | `part.get_payload(decode=True).decode(errors='ignore')` | `decode=True` reverses base64/quoted-printable encoding to raw bytes. `.decode(errors='ignore')` converts bytes to string, skipping unreadable characters. |
| 85 | `msg.get_payload(decode=True).decode(...)` | Same as above for simple, non-multipart emails with a single body payload. |
| 86 | `self.extract_dates_from_text(body)` | Searches the full assembled body text for dates. |
| 87 | `[f"Body: {d}" for d in body_dates]` | Labels each date so the output file shows it came from the email body. |

---

### `dateExtractor.py` — `extract_from_text_file()`

| # | Line | Explanation |
|---|---|---|
| 88 | `open(text_path, 'r', encoding='utf-8', errors='ignore')` | Opens in text read mode with UTF-8 encoding. `errors='ignore'` handles files with mixed or broken character encodings without crashing. |
| 89 | `text = f.read()` | Reads the entire file as one string and passes it directly to `extract_dates_from_text`. |
| 90 | `self.extract_dates_from_text(text)` | Runs the full regex + dateutil pipeline on the file's content. |

---

### `dateExtractor.py` — `process_file()`

| # | Line | Explanation |
|---|---|---|
| 91 | `file_path = Path(file_path)` | Converts the argument to a `Path` object so `.suffix`, `.exists()`, and other Path methods work reliably. |
| 92 | `file_path.suffix.lower()` | Gets the file extension (`.PDF` → `.pdf`) lowercased to ensure comparisons work regardless of capitalisation. |
| 93 | `dates = []` | Resets the dates list for this specific file. Each call to `process_file` starts fresh. |
| 94 | `if extension in ['.jpg', ...]:` | Routes the file to the correct extraction method by matching its extension. |
| 95 | `self.extract_from_image(file_path)` | Handles image files via the OCR pipeline. |
| 96 | `self.extract_from_pdf(file_path)` | Handles PDF files via PyPDF2 text extraction. |
| 97 | `self.extract_from_email(file_path)` | Handles `.eml`/`.msg` files via the email parser. |
| 98 | `self.extract_from_text_file(file_path)` | Handles `.txt`/`.md` files via direct plain text reading. |
| 99 | `self.extract_from_text_file(file_path)` *(fallback)* | Unknown extensions fall back to plain text — useful for forwarded messages saved without a standard extension. |
| 100 | `'file': str(file_path)` | Stores the filename as a string. `Path` objects must be explicitly converted to be written to files or serialised. |
| 101 | `'dates': dates` | Stores the found dates alongside the filename so both are written together in `save_results()`. |

---

### `dateExtractor.py` — `process_directory()` and `save_results()`

| # | Line | Explanation |
|---|---|---|
| 102 | `directory = Path(directory)` | Ensures the directory is a `Path` object so `.rglob()` can be called on it. |
| 103 | `directory.rglob('*')` | Recursively finds every item (files and folders) inside the directory and all its subdirectories. `*` matches everything. |
| 104 | `if file_path.is_file():` | Filters out subdirectory entries — only actual files are passed to `process_file`. |
| 105 | `open(self.output_file, 'w', encoding='utf-8')` | Opens the output file for writing with UTF-8 encoding so special characters like bullet `•` are written correctly. |
| 106 | `datetime.now().strftime('%Y-%m-%d %H:%M:%S')` | Gets the current timestamp and formats it as `2024-02-11 14:30:00`. Written in the report header so the run is traceable. |
| 107 | `"=" * 80` | Creates a horizontal divider of 80 `=` characters. Pure visual formatting for the report. |
| 108 | `if not self.extracted_dates:` | Checks if the result list is empty across all files. Writes a "No dates found" message if so. |
| 109 | `for item in self.extracted_dates:` | Iterates through results. Each `item` is a dict with keys `'file'` and `'dates'`. |
| 110 | `f.write(f"File: {item['file']}\n")` | Writes the source filename as a section header in the report. |
| 111 | `"-" * 80` | Creates a separator of 80 dashes beneath the filename. |
| 112 | `f"  • {date}\n"` | Writes each date with a bullet point and 2-space indent for visual clarity in the text file. |
| 113 | `f.write("\n")` | Adds a blank line after each file's section to separate them in the report. |
| 114 | `len(self.extracted_dates)` | Count of files that had at least one date (files with zero dates are excluded from the list). |
| 115 | `sum(len(item['dates']) for item in self.extracted_dates)` | Generator expression that sums the date counts across all files to get the grand total. |

---

### `main.py` — CLI Interface

| # | Line | Explanation |
|---|---|---|
| 116 | `from pathlib import Path` | Enables `path.is_file()` and `path.is_dir()` checks on the user-provided command-line arguments. |
| 117 | `import dateExtractor` | Imports the `dateExtractor` module. Both `main.py` and `dateExtractor.py` must be in the same directory. |
| 118 | `import sys` | Gives access to `sys.argv` — the list of everything the user typed when running the script. |
| 119 | `extractor = dateExtractor.DateExtractor(output_file="extracted_dates.txt")` | Creates a single `DateExtractor` instance for the whole run. All results from all files are stored inside this object. |
| 120 | `# sys.argv explanation` | `sys.argv[0]` = script name. `sys.argv[1:]` = user-provided paths. Running `python main.py a.pdf b.jpg` gives `sys.argv = ["main.py", "a.pdf", "b.jpg"]`. |
| 121 | `if len(sys.argv) < 2:` | Length 1 means only the script name is present. No files were given — show the help message. |
| 122 | `sys.exit(1)` | Exits with error code `1`. Convention: `0` = success, non-zero = error. Useful for shell scripts that check exit codes. |
| 123 | `for path in sys.argv[1:]:` | Iterates over every argument the user provided, skipping index 0 (the script name). |
| 124 | `path = Path(path)` | Converts the string argument to a `Path` object so `.is_file()` and `.is_dir()` work on it. |
| 125 | `if path.is_file():` | True if the path points to an existing file. Calls `process_file()`. |
| 126 | `elif path.is_dir():` | True if the path points to a folder. Calls `process_directory()` to handle all files inside recursively. |
| 127 | `print(f"Warning: {path} not found")` | If the path is neither a file nor a directory, it doesn't exist. We warn and continue rather than crash. |
| 128 | `extractor.save_results()` | Called once after all files are processed. Writes the final `extracted_dates.txt` report. |
| 129 | `if __name__ == "__main__":` | Python sets `__name__` to `"__main__"` only when the script is run directly. Prevents `main()` from running if this file is imported by another script. |

---

