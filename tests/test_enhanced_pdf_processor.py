#!/usr/bin/env python3
"""
Test script for enhanced PDF processor with OCR support and markdown output.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from docstrange.extractor import DocumentExtractor
from docstrange.processors.pdf_processor import PDFProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_pdf_processor_enhancements():
    """Test the enhanced PDF processor with OCR support and markdown output."""
    
    print("=" * 80)
    print("Testing Enhanced PDF Processor with OCR Support")
    print("=" * 80)
    
    # Initialize extractor with OCR enabled
    extractor = DocumentExtractor(
        preserve_layout=True,
        include_images=False,
        ocr_enabled=True
    )
    
    # Test with sample PDF files
    sample_files = [
        "sample_documents/sample.pdf",
        "sample_documents/sample_scanned.pdf",  # If available
    ]
    
    for file_path in sample_files:
        if not os.path.exists(file_path):
            print(f"\n⚠️  File not found: {file_path}")
            continue
            
        print(f"\n📄 Processing: {file_path}")
        print("-" * 60)
        
        try:
            # Process the PDF
            result = extractor.extract(file_path)
            
            print(f"✅ Processing successful!")
            print(f"📊 Metadata:")
            for key, value in result.metadata.items():
                if key != 'file_path':  # Skip long file path
                    print(f"   {key}: {value}")
            
            print(f"\n📝 Content Preview (first 500 chars):")
            print("-" * 40)
            content_preview = result.content[:500]
            if len(result.content) > 500:
                content_preview += "..."
            print(content_preview)
            
            # Save full content to file
            output_file = f"output_{Path(file_path).stem}_enhanced.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.content)
            print(f"\n💾 Full content saved to: {output_file}")
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            logger.error(f"Error processing {file_path}: {e}", exc_info=True)


def test_pdf_processor_directly():
    """Test the PDF processor directly with different configurations."""
    
    print("\n" + "=" * 80)
    print("Testing PDF Processor Directly")
    print("=" * 80)
    
    # Test files
    test_files = [
        "sample_documents/sample.pdf",
    ]
    
    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"\n⚠️  File not found: {file_path}")
            continue
            
        print(f"\n📄 Testing: {file_path}")
        print("-" * 60)
        
        # Test with OCR enabled
        print("🔍 Testing with OCR enabled...")
        processor_ocr = PDFProcessor(ocr_enabled=True)
        try:
            result_ocr = processor_ocr.process(file_path)
            print(f"✅ OCR processing successful!")
            print(f"   Pages with text: {result_ocr.metadata.get('pages_with_text', 'N/A')}")
            print(f"   Pages with OCR: {result_ocr.metadata.get('pages_with_ocr', 'N/A')}")
            print(f"   Total text length: {result_ocr.metadata.get('total_text_length', 'N/A')}")
        except Exception as e:
            print(f"❌ OCR processing failed: {e}")
        
        # Test with OCR disabled
        print("\n📝 Testing with OCR disabled...")
        processor_no_ocr = PDFProcessor(ocr_enabled=False)
        try:
            result_no_ocr = processor_no_ocr.process(file_path)
            print(f"✅ No-OCR processing successful!")
            print(f"   Pages with text: {result_no_ocr.metadata.get('pages_with_text', 'N/A')}")
            print(f"   Total text length: {result_no_ocr.metadata.get('total_text_length', 'N/A')}")
        except Exception as e:
            print(f"❌ No-OCR processing failed: {e}")


def test_ocr_capabilities():
    """Test OCR capabilities specifically."""
    
    print("\n" + "=" * 80)
    print("Testing OCR Capabilities")
    print("=" * 80)
    
    # Test with a sample image to verify OCR is working
    image_file = "sample_documents/sample.png"
    
    if os.path.exists(image_file):
        print(f"\n🖼️  Testing OCR with image: {image_file}")
        
        from docstrange.processors.image_processor import ImageProcessor
        
        processor = ImageProcessor(ocr_enabled=True)
        try:
            result = processor.process(image_file)
            print(f"✅ Image OCR successful!")
            print(f"📊 OCR metadata: {result.metadata.get('ocr_performed', False)}")
            print(f"📝 OCR text length: {result.metadata.get('ocr_text_length', 0)}")
            
            if result.metadata.get('ocr_text_length', 0) > 0:
                print(f"\n📄 OCR Text Preview:")
                print("-" * 40)
                content_preview = result.content[:300]
                if len(result.content) > 300:
                    content_preview += "..."
                print(content_preview)
            else:
                print("⚠️  No text detected in image")
                
        except Exception as e:
            print(f"❌ Image OCR failed: {e}")
    else:
        print(f"\n⚠️  Image file not found: {image_file}")


def test_paddleocr_model_download():
    """Test PaddleOCR model download functionality."""
    
    print("\n" + "=" * 80)
    print("Testing PaddleOCR Model Download")
    print("=" * 80)
    
    try:
        print("📥 Pre-downloading PaddleOCR models...")
        PDFProcessor.predownload_ocr_models()
        print("✅ PaddleOCR models downloaded successfully!")
    except Exception as e:
        print(f"❌ PaddleOCR model download failed: {e}")


def main():
    """Main test function."""
    
    print("🚀 Starting Enhanced PDF Processor Tests")
    print("=" * 80)
    
    # Test PaddleOCR model download
    test_paddleocr_model_download()
    
    # Test OCR capabilities
    test_ocr_capabilities()
    
    # Test PDF processor directly
    test_pdf_processor_directly()
    
    # Test full extractor
    test_pdf_processor_enhancements()
    
    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    main() 