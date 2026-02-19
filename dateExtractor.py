import re
import os
from datetime import datetime
from pathlib import Path
import email
from email import policy
import subprocess
import tempfile


# PIL and pytesseract for image OCR
try:
    from PIL import Image
    import pytesseract
    import sys
    if sys.platform == 'win32':
        tesseract_path = r'C:\Users\Varsh\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        os.environ['TESSDATA_PREFIX'] = r'C:\Users\Varsh\AppData\Local\Programs\Tesseract-OCR\tessdata'
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("Warning: PIL/pytesseract not available. Install with: pip install pillow pytesseract")

# PyPDF2 for PDF reading
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("Warning: PyPDF2 not available. Install with: pip install PyPDF2")

# dateutil for normalizing matched dates to YYYY-MM-DD
try:
    from dateutil import parser as date_parser
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False
    print("Warning: dateutil not available. Install with: pip install python-dateutil")


class DateExtractor:
    def __init__(self, output_file="extracted_dates.txt"):
        self.output_file = output_file
        self.extracted_dates = []

        self.date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',                                                                                                    # 01/15/2024
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',                                                                                                       # 2024-01-15
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',                                                         # Jan 15, 2024
            r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',                                                           # 15 Jan 2024
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2},? \d{4}\b',                         # January 15, 2024
            r'\b\d{1,2}(?:st|nd|rd|th)? (?:of )?(?:January|February|March|April|May|June|July|August|September|October|November|December),? \d{4}\b', # 1st of January 2024
            r'\b\d{1,2}(?:,\s*\d{1,2})+ (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',                                          # 25,26,27 FEB 2026
            r'\b\d{1,2}(?:,\s*\d{1,2})+ (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{4}\b',           # 25,26,27 February 2026
            r'\b\d{1,2}(?:st|nd|rd|th)?(?:\s*[&,]\s*\d{1,2}(?:st|nd|rd|th)?)* (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',
            r'\b\d{1,2}(?:st|nd|rd|th)?(?:\s*[&,]\s*\d{1,2}(?:st|nd|rd|th)?)* (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{4}\b', #18 & 19 february
            r'\b\d{1,2}(?:st|nd|rd|th)?\s*-\s*\d{1,2}(?:st|nd|rd|th)? (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*,? \d{4}\b',
            r'\b\d{1,2}(?:st|nd|rd|th)?\s*-\s*\d{1,2}(?:st|nd|rd|th)? (?:January|February|March|April|May|June|July|August|September|October|November|December),? \d{4}\b', #19 - 18 feb
        ]

        # Maps month names/abbreviations to 2-digit numbers for expand_multiday_dates()
        self.month_map = {
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
            'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'june': '06', 'july': '07', 'august': '08', 'september': '09',
            'october': '10', 'november': '11', 'december': '12'
        }

    def normalize_date(self, date_str):
        """
        Convert any matched date string into standard YYYY-MM-DD format.
        This ensures all dates are stored in one consistent format.
        Returns None if the string cannot be parsed as a date.
        """
        if not DATEUTIL_AVAILABLE:
            return None
        try:
            parsed = date_parser.parse(date_str, fuzzy=False)
            return parsed.strftime('%Y-%m-%d')
        except (ValueError, OverflowError, TypeError):
            return None

    def expand_multiday_dates(self, match_str):
        """
        Convert '25,26,27 FEB 2026' into ['2026-02-25', '2026-02-26', '2026-02-27'].
        Returns a list of individual YYYY-MM-DD strings, one per day.
        """
        try:
            parts = match_str.split(' ', 1)            # ['25,26,27', 'FEB 2026']
            days_part = parts[0]                        # '25,26,27'
            month_year = parts[1].strip().split()       # ['FEB', '2026']
            month_str = month_year[0].lower()[:3]       # 'feb'
            month_num = self.month_map.get(month_str)   # '02'
            year = month_year[1]                        # '2026'
            if not month_num:
                return []
            days = [d.strip() for d in days_part.split(',')]
            return [f"{year}-{month_num}-{day.zfill(2)}" for day in days]
        except Exception:
            return []
        
    
    def expand_daterange_with_dash(self, match_str):
        """
        Expands '7th - 8th March 2026' into ['2026-03-07', '2026-03-08'].
        Handles ordinal suffixes (st, nd, rd, th) and extracts start/end days.
        """
        try:
            # Remove ordinal suffixes: "7th - 8th March 2026" → "7 - 8 March 2026"
            clean = re.sub(r'(\d+)(?:st|nd|rd|th)', r'\1', match_str)
            
            # Split on the dash to get: "7" and "8 March 2026"
            parts = clean.split('-')
            start_day = int(parts[0].strip())
            
            # parts[1] = "8 March 2026" → split to get end_day and month/year
            rest = parts[1].strip().split()
            end_day = int(rest[0])
            month_str = rest[1].rstrip(',').lower()[:3]
            year = rest[2]
            
            month_num = self.month_map.get(month_str)
            if not month_num:
                return []
            
            # Generate all dates in the range
            return [f"{year}-{month_num}-{str(d).zfill(2)}" for d in range(start_day, end_day + 1)]
        except Exception:
            return []
        

    def extract_dates_from_text(self, text):
        """
        Find all dates in a string.

        Key design: every date is normalized to YYYY-MM-DD before saving.
        A 'seen' set tracks which dates have already been added.
        This means no matter how many patterns or methods match the same
        date, it will only appear ONCE in the output.
        """

        # --- PRE-PROCESSING ---
        # Tesseract OCR reads text line by line. A date like:
        #     25,26,27        <- line 1
        #     FEB 2026        <- line 2
        # becomes "25,26,27\nFEB 2026" in the string, which no pattern matches.
        # These substitutions join such split dates back into a single line.

        # Case 1: day numbers on one line, month (+ optional year) on the next
        text = re.sub(
            r'(\b\d{1,2}(?:[,\s]*\d{1,2})*)\s*\n\s*'
            r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*(?:\s+\d{4})?)',
            r'\1 \2', text, flags=re.IGNORECASE
        )
        # Case 2: month on one line, year on the next  e.g. "FEB\n2026"
        text = re.sub(
            r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)\s*\n\s*(\d{4}\b)',
            r'\1 \2', text, flags=re.IGNORECASE
        )

        # --- EXTRACTION ---
        dates = []
        seen = set()  # YYYY-MM-DD strings already saved — the deduplication gate

        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:

                if re.match(r'^\d{1,2}(?:,\s*\d{1,2})+', match):
                    # Comma-separated: "25,26,27 FEB 2026"
                    for date_str in self.expand_multiday_dates(match):
                        if date_str not in seen:
                            seen.add(date_str)
                            dates.append(date_str)
                elif re.match(r'^\d{1,2}(?:st|nd|rd|th)?\s*-', match):
                    # Dash range: "7th - 8th March 2026"
                    for date_str in self.expand_daterange_with_dash(match):
                        if date_str not in seen:
                            seen.add(date_str)
                            dates.append(date_str)
        
                else:
                    # Single date — normalize to YYYY-MM-DD, skip if already seen
                    normalized = self.normalize_date(match)
                    if normalized:
                        if normalized not in seen:
                            seen.add(normalized)
                            dates.append(normalized)
                    else:
                        # Normalization failed — store raw match as fallback
                        if match not in seen:
                            seen.add(match)
                            dates.append(match)

        return dates
    
    def extract_text_by_fontsize(self, image_path):
        tesseract_cmd = r'C:\Users\Varsh\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
        env = os.environ.copy()
        env['TESSDATA_PREFIX'] = r'C:\Users\Varsh\AppData\Local\Programs\Tesseract-OCR\tessdata'

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            out_base = tmp.name.replace('.txt', '')

        # Run Tesseract with TSV output — gives us word positions and heights
        subprocess.run(
            [tesseract_cmd, str(image_path), out_base, 'tsv'],
            env=env, capture_output=True, text=True
        )

        tsv_file = out_base + '.tsv'
        if not os.path.exists(tsv_file):
            return None  # fall back to plain OCR

        # Parse the TSV file
        lines_dict = {}  # key=(block,par,line) → {'height': max_height, 'words': []}
        with open(tsv_file, 'r', encoding='utf-8') as f:
            headers = f.readline().strip().split('\t')  # skip header row
            for row in f:
                cols = row.strip().split('\t')
                if len(cols) < 12:
                    continue
                try:
                    height = int(cols[8])   # bounding box height = font size proxy
                    conf   = int(cols[10])  # confidence score
                    word   = cols[11]       # the recognised word
                except (ValueError, IndexError):
                    continue

                if conf < 30 or not word.strip():  # skip low-confidence or empty words
                    continue

                block = cols[2]; par = cols[3]; line = cols[4]
                key = (block, par, line)
                if key not in lines_dict:
                    lines_dict[key] = {'height': 0, 'words': []}
                lines_dict[key]['words'].append(word)
                lines_dict[key]['height'] = max(lines_dict[key]['height'], height)

        os.remove(tsv_file)

        if not lines_dict:
            return None

        # Sort lines largest font first, then join into a single string
        sorted_lines = sorted(lines_dict.values(), key=lambda x: x['height'], reverse=True)
        return '\n'.join(' '.join(l['words']) for l in sorted_lines)


    def extract_event_name(self, image_path):
        """
        Returns the largest text from the image that isn't a date.
        This is assumed to be the event/poster title.
        Falls back to filename if TSV parsing fails.
        """


        tesseract_cmd = r'C:\Users\Varsh\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
        env = os.environ.copy()
        env['TESSDATA_PREFIX'] = r'C:\Users\Varsh\AppData\Local\Programs\Tesseract-OCR\tessdata'

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            out_base = tmp.name.replace('.txt', '')

        subprocess.run(
            [tesseract_cmd, str(image_path), out_base, 'tsv'],
            env=env, capture_output=True, text=True
        )

        tsv_file = out_base + '.tsv'
        if not os.path.exists(tsv_file):
            return Path(image_path).stem  # fallback to filename

        # Parse TSV and group by lines, track max height
        lines_dict = {}
        with open(tsv_file, 'r', encoding='utf-8') as f:
            f.readline()  # skip header
            for row in f:
                cols = row.strip().split('\t')
                if len(cols) < 12:
                    continue
                try:
                    height = int(cols[8])
                    conf = int(cols[10])
                    word = cols[11]
                except (ValueError, IndexError):
                    continue
                if conf < 30 or not word.strip():
                    continue

                block, par, line = cols[2], cols[3], cols[4]
                key = (block, par, line)
                if key not in lines_dict:
                    lines_dict[key] = {'height': 0, 'words': []}
                lines_dict[key]['words'].append(word)
                lines_dict[key]['height'] = max(lines_dict[key]['height'], height)

        os.remove(tsv_file)

        if not lines_dict:
            return Path(image_path).stem

        # Sort by height, get the largest non-date line
        sorted_lines = sorted(lines_dict.values(), key=lambda x: x['height'], reverse=True)
        
        for line in sorted_lines:
            text = ' '.join(line['words'])
            # Skip if this line looks like a date (contains month names or lots of numbers)
            if any(month in text.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                                                        'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                continue
            if sum(c.isdigit() for c in text) > len(text) / 2:  # more than 50% numbers
                continue
            # This looks like the title
            return text.strip()

        # Fallback if all large text looks like dates
        print(f"Extracted text from {image_path}")
        event_name = self.extract_event_name(image_path)
        dates = self.extract_dates_from_text(text_to_use)
        return {'event_name': event_name, 'dates': dates}


    def extract_from_image(self, image_path):
        """Extract text from image using OCR, then extract dates"""
        if not OCR_AVAILABLE:
            print(f"Skipping image {image_path}: OCR not available")
            return []

        try:
            import subprocess
            import tempfile

            tesseract_cmd = r'C:\Users\Varsh\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
            image_path_str = str(image_path)

            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
                output_file = tmp.name

            env = os.environ.copy()
            env['TESSDATA_PREFIX'] = r'C:\Users\Varsh\AppData\Local\Programs\Tesseract-OCR\tessdata'

            cmd = [tesseract_cmd, image_path_str, output_file.replace('.txt', '')]
            subprocess.run(cmd, env=env, capture_output=True, text=True)

            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    plain_text = f.read()
                os.remove(output_file)

                # Try font-size aware extraction first (largest text = most important date)
                sized_text = self.extract_text_by_fontsize(image_path)
                text_to_use = sized_text if sized_text else plain_text

                print(f"Extracted text from {image_path}")
                return self.extract_dates_from_text(text_to_use)
            else:
                print(f"Error processing image {image_path}: No output from tesseract")
                return []
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")
            return []

    def extract_from_pdf(self, pdf_path):
        """Extract text from PDF, then extract dates"""
        if not PDF_AVAILABLE:
            print(f"Skipping PDF {pdf_path}: PyPDF2 not available")
            return []

        try:
            dates = []
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    page_dates = self.extract_dates_from_text(text)
                    dates.extend([f"{d} (page {page_num + 1})" for d in page_dates])
            print(f"Extracted dates from {pdf_path}")
            return dates
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {e}")
            return []

    def extract_from_email(self, email_path):
        """Extract dates from email file"""
        try:
            with open(email_path, 'rb') as f:
                msg = email.message_from_binary_file(f, policy=policy.default)

            dates = []

            if msg['Date']:
                dates.append(f"Email Date: {msg['Date']}")

            if msg['Subject']:
                subject_dates = self.extract_dates_from_text(msg['Subject'])
                dates.extend([f"Subject: {d}" for d in subject_dates])

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body += part.get_payload(decode=True).decode(errors='ignore')
            else:
                body = msg.get_payload(decode=True).decode(errors='ignore')

            body_dates = self.extract_dates_from_text(body)
            dates.extend([f"Body: {d}" for d in body_dates])

            print(f"Extracted dates from email {email_path}")
            return dates
        except Exception as e:
            print(f"Error processing email {email_path}: {e}")
            return []

    def extract_from_text_file(self, text_path):
        """Extract dates from plain text file"""
        try:
            with open(text_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            dates = self.extract_dates_from_text(text)
            print(f"Extracted dates from {text_path}")
            return dates
        except Exception as e:
            print(f"Error processing text file {text_path}: {e}")
            return []

    def process_file(self, file_path):
        """Process a single file based on its extension"""
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        dates = []

        if extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
            dates = self.extract_from_image(file_path)
        elif extension == '.pdf':
            dates = self.extract_from_pdf(file_path)
        elif extension in ['.eml', '.msg']:
            dates = self.extract_from_email(file_path)
        elif extension in ['.txt', '.text', '.md']:
            dates = self.extract_from_text_file(file_path)
        else:
            print(f"Unknown extension {extension}, attempting to read as text...")
            dates = self.extract_from_text_file(file_path)

        if dates:
        # Handle both old format (list) and new format (dict with event_name)
            if isinstance(dates, dict) and 'event_name' in dates:
                self.extracted_dates.append({
                    'file': str(file_path),
                    'event_name': dates['event_name'],
                    'dates': dates['dates']
                })
            else:
                # Fallback for PDFs/emails/text files (no event name extraction yet)
                self.extracted_dates.append({
                    'file': str(file_path),
                    'event_name': Path(file_path).stem,
                    'dates': dates if isinstance(dates, list) else []
                })

        return dates

    def process_directory(self, directory):
        """Process all supported files in a directory"""
        directory = Path(directory)
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                self.process_file(file_path)

    def save_results(self):
        """Save all extracted dates to output file"""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(f"Date Extraction Results\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

            if not self.extracted_dates:
                f.write("No dates found.\n")
            else:
                for item in self.extracted_dates:
                    event_name = item.get('event_name', 'Unknown Event')
                    f.write(f"Event: {event_name}\n")
                    f.write(f"File: {item['file']}\n")
                    f.write("-" * 80 + "\n")
                    for date in item['dates']:
                        f.write(f"  • {date}\n")
                    f.write("\n")

        print(f"\nResults saved to: {self.output_file}")
        print(f"Total files processed: {len(self.extracted_dates)}")
        total_dates = sum(len(item['dates']) for item in self.extracted_dates)
        print(f"Total dates found: {total_dates}")