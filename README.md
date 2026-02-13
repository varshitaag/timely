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
