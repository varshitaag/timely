from pathlib import Path
import dateExtractor
import sys


def main():
    """Main function - example usage"""
    
    extractor = dateExtractor.DateExtractor(output_file="extracted_dates.txt")
    
    if len(sys.argv) < 2: # No files were provided - show the help message and exit
        print("Usage: python date_extractor.py <file_or_directory> [file2] [file3] ...")
        print("\nExample:")
        print("  python date_extractor.py document.pdf")
        print("  python date_extractor.py image.jpg email.eml")
        print("  python date_extractor.py ./documents/")
        print("\nSupported formats:")
        print("  - Images: .jpg, .png, .gif, .bmp, .tiff (requires pytesseract)")
        print("  - PDFs: .pdf (requires PyPDF2)")
        print("  - Emails: .eml, .msg")
        print("  - Text: .txt, .md, or any text file")
        sys.exit(1)
    
    # Process each argument
    for path in sys.argv[1:]:
        path = Path(path)
        
        if path.is_file():
            extractor.process_file(path)
        elif path.is_dir():
            extractor.process_directory(path)
        else:
            print(f"Warning: {path} not found")
    
    # Save results
    extractor.save_results()


if __name__ == "__main__":
    main()