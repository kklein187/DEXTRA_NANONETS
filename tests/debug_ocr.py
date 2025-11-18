#!/usr/bin/env python3
"""Debug script for OCR functionality."""

import logging
import os
from docstrange import DocumentExtractor

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_ocr_debug():
    """Test OCR with detailed debugging."""
    print("🔍 OCR Debug Test")
    print("=" * 50)
    
    # Create a simple test image with text
    from PIL import Image, ImageDraw, ImageFont
    import tempfile
    
    # Create a test image with text
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a font, fallback to default if not available
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except:
            font = ImageFont.load_default()
    
    # Add some text to the image
    draw.text((50, 50), "Hello World!", fill='black', font=font)
    draw.text((50, 100), "This is a test image", fill='black', font=font)
    draw.text((50, 150), "for OCR testing", fill='black', font=font)
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        img.save(tmp.name)
        test_image_path = tmp.name
    
    print(f"📸 Created test image: {test_image_path}")
    print(f"📏 Image size: {img.size}")
    
    try:
        # Test OCR directly
        print("\n🤖 Testing OCR Service Directly")
        print("-" * 30)
        
        from docstrange.services.ocr_service import OCRServiceFactory
        
        ocr_service = OCRServiceFactory.create_service()
        print("✅ OCR service created")
        
        # Test simple OCR
        print("\n📝 Testing simple OCR...")
        simple_result = ocr_service.extract_text(test_image_path)
        print(f"Simple OCR result: '{simple_result}'")
        
        # Test layout-aware OCR
        print("\n📋 Testing layout-aware OCR...")
        layout_result = ocr_service.extract_text_with_layout(test_image_path)
        print(f"Layout OCR result: '{layout_result}'")
        
        # Test with extractor
        print("\n🔄 Testing with DocumentExtractor...")
        extractor = DocumentExtractor(ocr_enabled=True)
        result = extractor.extract(test_image_path)
        print(f"Converter result: '{result.content}'")
        
    except Exception as e:
        print(f"❌ Error during OCR test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        if os.path.exists(test_image_path):
            os.unlink(test_image_path)
            print(f"🧹 Cleaned up test image")

if __name__ == "__main__":
    test_ocr_debug() 