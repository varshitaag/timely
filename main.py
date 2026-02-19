from pathlib import Path   # [116] 'Path' for safe, cross-platform file path handling
import dateExtractor       # [117] Import our dateExtractor module (dateExtractor.py must be in the same folder)
import sys                 # [118] 'sys' lets us read the command-line arguments the user types after the script name


def main():
    """Entry point: reads file arguments from the terminal, processes them, and saves results"""

    # [119] Create a DateExtractor instance — all results will accumulate inside this object.
    # output_file sets the name of the text file where dates will be saved.
    extractor = dateExtractor.DateExtractor(output_file="extracted_dates.txt")

    # [120] sys.argv is a list of everything the user typed in the terminal.
    # sys.argv[0] = script name ("main.py")
    # sys.argv[1], sys.argv[2], ... = the files/folders the user passed in
    # Example: "python main.py invoice.pdf screenshot.jpg"
    # → sys.argv = ["main.py", "invoice.pdf", "screenshot.jpg"]
    if len(sys.argv) < 2:   # [121] If only the script name is present, no files were given — show help
        print("Usage: python main.py <file_or_directory> [file2] [file3] ...")
        print("\nExample:")
        print("  python main.py document.pdf")
        print("  python main.py image.jpg email.eml")
        print("  python main.py ./documents/")
        print("\nSupported formats:")
        print("  - Images : .jpg  .png  .gif  .bmp  .tiff  (requires pytesseract + Tesseract)")
        print("  - PDFs   : .pdf                            (requires PyPDF2)")
        print("  - Emails : .eml  .msg")
        print("  - Text   : .txt  .md  or any plain text file")
        sys.exit(1)  # [122] Exit with code 1 to signal an error (0 = success, non-zero = something went wrong)

    # [123] sys.argv[1:] skips the script name at index 0 and gives us only the user-provided paths
    for path in sys.argv[1:]:
        path = Path(path)   # [124] Convert the string argument to a Path object for is_file() / is_dir() checks

        if path.is_file():         # [125] The argument points to a single file — process it directly
            extractor.process_file(path)
        elif path.is_dir():        # [126] The argument points to a folder — process all files inside recursively
            extractor.process_directory(path)
        else:
            print(f"Warning: {path} not found")   # [127] Path doesn't exist — warn and continue with remaining arguments

    extractor.save_results()  # [128] After all files are processed, write everything collected to extracted_dates.txt


# [129] This guard ensures main() only runs when this script is executed directly.
# If another script imports main.py, main() will NOT be called automatically.
if __name__ == "__main__":
    main()