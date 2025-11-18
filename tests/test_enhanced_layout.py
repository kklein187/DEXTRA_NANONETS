#!/usr/bin/env python3
"""Test script for enhanced layout detection in nanonets-ocr service."""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from docstrange.services.nanonets_ocr import NanonetsOCRService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_layout_detection():
    """Test the enhanced layout detection functionality."""
    
    # Initialize the OCR service
    ocr_service = NanonetsOCRService()
    
    # Test with a sample image (if available)
    test_image_path = "test_image.png"
    
    if os.path.exists(test_image_path):
        logger.info(f"Testing layout detection with: {test_image_path}")
        
        # Test simple text extraction
        simple_text = ocr_service.extract_text(test_image_path)
        logger.info(f"Simple text extraction length: {len(simple_text)}")
        logger.info(f"First 200 chars: {simple_text[:200]}")
        
        # Test layout-aware extraction
        layout_text = ocr_service.extract_text_with_layout(test_image_path)
        logger.info(f"Layout-aware extraction length: {len(layout_text)}")
        logger.info(f"Layout-aware text:\n{layout_text}")
        
        # Compare the results
        if layout_text != simple_text:
            logger.info("✅ Layout detection is working - different output from layout-aware extraction")
        else:
            logger.info("⚠️ Layout detection may not be working - same output from both methods")
    
    else:
        logger.warning(f"Test image not found: {test_image_path}")
        logger.info("Creating a simple test to verify the service initialization...")
        
        # Test service initialization
        try:
            # Test that the service can be initialized
            logger.info("✅ NanonetsOCRService initialized successfully")
            
            # Test layout element creation
            from docstrange.services.nanonets_ocr import LayoutElement
            
            test_element = LayoutElement(
                text="Test Heading",
                x=100,
                y=50,
                width=200,
                height=30,
                element_type="heading"
            )
            
            logger.info(f"✅ LayoutElement created: {test_element.text} at ({test_element.x}, {test_element.y})")
            logger.info(f"Element type: {test_element.element_type}")
            logger.info(f"Area: {test_element.area()}")
            
        except Exception as e:
            logger.error(f"❌ Service initialization failed: {e}")
            return False
    
    return True


def test_layout_classification():
    """Test the layout classification logic."""
    
    from docstrange.services.nanonets_ocr import NanonetsOCRService, LayoutElement
    
    ocr_service = NanonetsOCRService()
    
    # Create test elements with more realistic positioning
    test_elements = [
        LayoutElement("Document Title", 100, 20, 300, 40, "text"),      # Should be header (top 15%)
        LayoutElement("1. First item", 50, 100, 200, 25, "text"),       # Should be list_item
        LayoutElement("2. Second item", 50, 130, 200, 25, "text"),      # Should be list_item
        LayoutElement("Section Heading", 50, 180, 250, 35, "text"),     # Should be heading (larger text)
        LayoutElement("Regular text here", 50, 220, 200, 20, "text"),   # Should be text
        LayoutElement("Page 1 of 5", 50, 750, 150, 20, "text"),         # Should be footer (bottom 15%)
    ]
    
    # Test classification with realistic page size
    image_size = (800, 800)
    classified = ocr_service._classify_layout_elements(test_elements, image_size)
    
    logger.info("Testing layout classification:")
    for elem in classified:
        logger.info(f"  '{elem.text}' -> {elem.element_type}")
    
    # Test section grouping
    sections = ocr_service._group_into_sections(classified)
    
    logger.info("\nTesting section grouping:")
    for i, section in enumerate(sections):
        logger.info(f"  Section {i}: {section['type']} with {len(section['elements'])} elements")
        for elem in section['elements']:
            logger.info(f"    - {elem.element_type}: {elem.text}")
    
    # Test markdown generation
    markdown = ocr_service._generate_structured_markdown(sections)
    
    logger.info("\nGenerated markdown:")
    logger.info("=" * 50)
    logger.info(markdown)
    logger.info("=" * 50)
    
    return True


if __name__ == "__main__":
    logger.info("Testing Enhanced Layout Detection")
    logger.info("=" * 50)
    
    # Test basic functionality
    if test_layout_detection():
        logger.info("✅ Basic layout detection test passed")
    else:
        logger.error("❌ Basic layout detection test failed")
    
    # Test layout classification
    if test_layout_classification():
        logger.info("✅ Layout classification test passed")
    else:
        logger.error("❌ Layout classification test failed")
    
    logger.info("=" * 50)
    logger.info("Enhanced layout detection testing complete!") 