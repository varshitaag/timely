import re
import os
from datetime import datetime
from pathlib import Path
import email
from email import policy
from tkinter import Image

try:
    from PIL import Image
    import pytesseract
    # Configure Tesseract path for Windows
    import sys
    if sys.platform == 'win32':
        # Set tesseract path and tessdata directory
        tesseract_path = r'C:\Users\Varsh\Desktop\tesseract.exe'
        pytesseract.pytesseract.pytesseract_cmd = tesseract_path
        # Set TESSDATA_PREFIX environment variable for language data (must point to tessdata folder)
        os.environ['TESSDATA_PREFIX'] = r'C:\Users\Varsh\Desktop\tessdata'
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("Warning: PIL/pytesseract not available. Install with: pip install pillow pytesseract")

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("Warning: PyPDF2 not available. Install with: pip install PyPDF2")

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
        
        # Common date patterns (regex)
        self.date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or DD/MM/YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',     # YYYY/MM/DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month DD, YYYY
            r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',    # DD Month YYYY
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2},? \d{4}\b',
            r'\b\d{1,2}(?:st|nd|rd|th)? (?:of )?(?:January|February|March|April|May|June|July|August|September|October|November|December),? \d{4}\b',
        ]
    
    def extract_dates_from_text(self, text):
        """Extract dates from text using regex patterns"""
        dates = []
        
        # Try regex patterns
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        # If dateutil is available, use it for more robust parsing
        if DATEUTIL_AVAILABLE:
            words = text.split()
            for i in range(len(words)):
                # Try parsing combinations of 1-4 consecutive words
                for length in range(1, min(5, len(words) - i + 1)):
                    try:
                        phrase = ' '.join(words[i:i+length])
                        parsed_date = date_parser.parse(phrase, fuzzy=False)
                        date_str = parsed_date.strftime('%Y-%m-%d')
                        if date_str not in [d.split()[0] if ' ' in d else d for d in dates]:
                            dates.append(f"{date_str} ({phrase})")
                    except (ValueError, OverflowError):
                        continue
        
        return dates
    
    def extract_from_image(self, image_path):
        """Extract text from image using OCR, then extract dates"""
        if not OCR_AVAILABLE:
            print(f"Skipping image {image_path}: OCR not available")
            return []
        
        try:
            import subprocess
            import tempfile
            
            # Use subprocess to call tesseract directly
            tesseract_cmd = r'C:\Users\Varsh\Desktop\tesseract.exe'
            image_path_str = str(image_path)
            
            # Create temporary output file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
                output_file = tmp.name
            
            # Call tesseract with proper environment
            env = os.environ.copy()
            env['TESSDATA_PREFIX'] = r'C:\Users\Varsh\Desktop\tessdata'
            
            # Run tesseract: tesseract image.jpg output
            cmd = [tesseract_cmd, image_path_str, output_file.replace('.txt', '')]
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            # Read the output file
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                os.remove(output_file)
                print(f"Extracted text from {image_path}")
                return self.extract_dates_from_text(text)
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
            
            # Get email date
            if msg['Date']:
                dates.append(f"Email Date: {msg['Date']}")
            
            # Extract from subject
            if msg['Subject']:
                subject_dates = self.extract_dates_from_text(msg['Subject'])
                dates.extend([f"Subject: {d}" for d in subject_dates])
            
            # Extract from body
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
            # Try as text file
            print(f"Unknown extension {extension}, attempting to read as text...")
            dates = self.extract_from_text_file(file_path)
        
        if dates:
            self.extracted_dates.append({
                'file': str(file_path),
                'dates': dates
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
                    f.write(f"File: {item['file']}\n")
                    f.write("-" * 80 + "\n")
                    for date in item['dates']:
                        f.write(f"  • {date}\n")
                    f.write("\n")
        
        print(f"\nResults saved to: {self.output_file}")
        print(f"Total files processed: {len(self.extracted_dates)}")
        total_dates = sum(len(item['dates']) for item in self.extracted_dates)
        print(f"Total dates found: {total_dates}")