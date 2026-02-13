#!/usr/bin/env python
import os
import sys

# Set up Tesseract paths
os.environ['TESSDATA_PREFIX'] = r'C:\Users\Varsh\Desktop\tessdata'

import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r'C:\Users\Varsh\Desktop\tesseract.exe'

from PIL import Image

try:
    print("Testing Tesseract configuration...")
    print(f"Tesseract executable: {pytesseract.pytesseract.pytesseract_cmd}")
    print(f"TESSDATA_PREFIX: {os.environ.get('TESSDATA_PREFIX')}")
    
    img = Image.open('data_for_timely_page-0001.jpg')
    print(f"Image loaded: {img.size}")
    
    text = pytesseract.image_to_string(img)
    print(f"Extracted text length: {len(text)}")
    print("First 200 characters:")
    print(text[:200])
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
