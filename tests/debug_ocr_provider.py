#!/usr/bin/env python3
import logging
from docstrange import DocumentExtractor
from docstrange.config import InternalConfig

# Set up detailed logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

print("=== OCR Provider Debug ===")
print(f"Default OCR provider: {InternalConfig.ocr_provider}")

file_path = "sample_documents/sample.png"

print(f"\n=== Testing with file: {file_path} ===")

extractor = DocumentExtractor()

# Test the conversion
result = extractor.extract(file_path).extract_markdown()

print("\n📝=============================== Markdown Output:===============================")
print(result) 