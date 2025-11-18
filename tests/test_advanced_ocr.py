#!/usr/bin/env python3
"""Test script for the new Advanced OCR service with docling's pre-trained models."""

import logging
import sys
from pathlib import Path
from docstrange import DocumentExtractor
from docstrange.config import InternalConfig

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_advanced_ocr():
    """Test the advanced OCR service."""
    try:
        from docstrange.services.advanced_ocr import AdvancedOCRService
        
        # Initialize the advanced OCR service
        logger.info("Initializing Advanced OCR Service...")
        ocr_service = AdvancedOCRService()
        
        # Test with a sample image
        test_image = "sample_documents/sample.png"
        
        if not Path(test_image).exists():
            logger.error(f"Test image not found: {test_image}")
            logger.info("Please place a test image at sample_documents/sample.png")
            return
        
        logger.info(f"Testing with image: {test_image}")
        
        # Test basic text extraction
        logger.info("Testing basic text extraction...")
        text = ocr_service.extract_text(test_image)
        print("📝=============================== Basic Text Output:===============================")
        print(text)
        print("=" * 80)
        
        # Test layout-aware text extraction
        logger.info("Testing layout-aware text extraction...")
        layout_text = ocr_service.extract_text_with_layout(test_image)
        print("📝=============================== Layout-Aware Markdown Output:===============================")
        print(layout_text)
        print("=" * 80)
        
        logger.info("Advanced OCR test completed successfully!")
        
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        logger.info("Please install the required dependencies:")
        logger.info("pip install huggingface_hub easyocr tqdm torch torchvision")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_ocr_service_factory():
    """Test the OCR service factory with different providers."""
    try:
        from docstrange.services.ocr_service import OCRServiceFactory
        
        logger.info("Testing OCR Service Factory...")
        
        # Test available providers
        providers = OCRServiceFactory.get_available_providers()
        logger.info(f"Available providers: {providers}")
        
        # Test creating advanced OCR service
        logger.info("Creating Advanced OCR service...")
        advanced_ocr = OCRServiceFactory.create_service('advanced')
        logger.info("Advanced OCR service created successfully")
        
        # Test creating nanonets OCR service
        logger.info("Creating Nanonets OCR service...")
        nanonets_ocr = OCRServiceFactory.create_service('nanonets')
        logger.info("Nanonets OCR service created successfully")
        
        logger.info("OCR Service Factory test completed successfully!")
        
    except Exception as e:
        logger.error(f"OCR Service Factory test failed: {e}")
        import traceback
        traceback.print_exc()

def test_model_downloader():
    """Test the model downloader."""
    try:
        from docstrange.services.model_downloader import ModelDownloader
        
        logger.info("Testing Model Downloader...")
        
        # Initialize model downloader
        downloader = ModelDownloader()
        
        # Test downloading models
        logger.info("Downloading models (this may take a while on first run)...")
        models_path = downloader.download_models(force=False, progress=True)
        logger.info(f"Models downloaded to: {models_path}")
        
        # Test getting model paths
        layout_path = downloader.get_model_path('layout')
        table_path = downloader.get_model_path('table')
        ocr_path = downloader.get_model_path('ocr')
        
        logger.info(f"Layout model path: {layout_path}")
        logger.info(f"Table model path: {table_path}")
        logger.info(f"OCR model path: {ocr_path}")
        
        logger.info("Model Downloader test completed successfully!")
        
    except Exception as e:
        logger.error(f"Model Downloader test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    logger.info("Starting Advanced OCR tests...")
    
    # Test model downloader
    test_model_downloader()
    print("\n" + "=" * 80 + "\n")
    
    # Test OCR service factory
    test_ocr_service_factory()
    print("\n" + "=" * 80 + "\n")
    
    # Test advanced OCR
    test_advanced_ocr()
    
    logger.info("All tests completed!")

print("=== Testing Advanced OCR Provider ===")

# Temporarily change the OCR provider
original_provider = InternalConfig.ocr_provider
InternalConfig.ocr_provider = 'advanced'

print(f"OCR provider set to: {InternalConfig.ocr_provider}")

file_path = "sample_documents/sample.png"

print(f"\n=== Testing with file: {file_path} ===")

try:
    extractor = DocumentExtractor()
    
    # Test the conversion
    result = extractor.extract(file_path).extract_markdown()
    
    print("\n📝=============================== Advanced OCR Output:===============================")
    print(result)
    
except Exception as e:
    print(f"Error with advanced OCR: {e}")
    import traceback
    traceback.print_exc()

finally:
    # Restore original provider
    InternalConfig.ocr_provider = original_provider
    print(f"\nRestored OCR provider to: {InternalConfig.ocr_provider}") 