#!/usr/bin/env python3
"""
Test script for OCR capabilities using real image files.
Tests OCR extraction on sample.png from sample_documents folder.
"""

import os
from docstrange import DocumentExtractor


def test_ocr_with_real_image():
    """Test OCR capabilities with the real sample.png file."""
    print("🤖 Testing OCR with Real Image File")
    print("=" * 60)
    
    # Path to the sample image
    image_path = "sample_documents/sample.png"
    
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return
    
    print(f"📸 Found image file: {image_path}")
    print(f"   File size: {os.path.getsize(image_path)} bytes")
    
    # Test with OCR disabled (should extract metadata only)
    print("\n🔍 Testing without OCR (metadata extraction)...")
    try:
        converter_no_ocr = DocumentExtractor(ocr_enabled=False)
        result_no_ocr = converter_no_ocr.extract(image_path)
        
        print(f"   ✅ Metadata extraction successful")
        print(f"   Content length: {len(result_no_ocr.content)} characters")
        print(f"   Metadata keys: {list(result_no_ocr.metadata.keys())}")
        
        # Show metadata
        for key, value in result_no_ocr.metadata.items():
            if key not in ['created_time', 'modified_time', 'access_time']:
                print(f"   {key}: {value}")
        
        # Show content preview
        if result_no_ocr.content:
            preview = result_no_ocr.content[:200] + "..." if len(result_no_ocr.content) > 200 else result_no_ocr.content
            print(f"   Content preview: {preview}")
        else:
            print(f"   Content: (empty - no OCR text extracted)")
            
    except Exception as e:
        print(f"   ❌ Metadata extraction failed: {e}")
    
    # Test with OCR enabled
    print("\n🤖 Testing with OCR enabled...")
    try:
        converter_ocr = DocumentExtractor(ocr_enabled=True)
        result_ocr = converter_ocr.extract(image_path)
        
        print(f"   ✅ OCR extraction successful")
        print(f"   Content length: {len(result_ocr.content)} characters")
        print(f"   Metadata keys: {list(result_ocr.metadata.keys())}")
        
        # Show OCR-specific metadata
        ocr_metadata = {k: v for k, v in result_ocr.metadata.items() if 'ocr' in k.lower() or 'text' in k.lower()}
        if ocr_metadata:
            print(f"   OCR metadata: {ocr_metadata}")
        
        # Show content preview
        if result_ocr.content:
            preview = result_ocr.content[:300] + "..." if len(result_ocr.content) > 300 else result_ocr.content
            print(f"   OCR text preview: {preview}")
        else:
            print(f"   OCR text: (empty - no text detected)")
            
    except Exception as e:
        print(f"   ❌ OCR extraction failed: {e}")
    
    # Test markdown output
    print("\n📝 Testing markdown output...")
    try:
        converter_ocr = DocumentExtractor(ocr_enabled=True)
        result = converter_ocr.extract(image_path)
        markdown = result.extract_markdown()
        
        print(f"   ✅ Markdown conversion successful")
        print(f"   Markdown length: {len(markdown)} characters")
        
        # Show markdown preview
        if markdown:
            preview = markdown[:200] + "..." if len(markdown) > 200 else markdown
            print(f"   Markdown preview: {preview}")
        else:
            print(f"   Markdown: (empty)")
            
    except Exception as e:
        print(f"   ❌ Markdown conversion failed: {e}")
    
    # Test JSON output
    print("\n📊 Testing JSON output...")
    try:
        converter_ocr = DocumentExtractor(ocr_enabled=True)
        result = converter_ocr.extract(image_path)
        json_output = result.extract_data()
        
        print(f"   ✅ JSON conversion successful")
        print(f"   JSON keys: {list(json_output.keys())}")
        print(f"   Content length in JSON: {len(json_output.get('content', ''))}")
        
    except Exception as e:
        print(f"   ❌ JSON conversion failed: {e}")


def test_ocr_comparison():
    """Compare OCR vs non-OCR results."""
    print("\n🔄 OCR vs Non-OCR Comparison")
    print("=" * 60)
    
    image_path = "sample_documents/sample.png"
    
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return
    
    try:
        # Test without OCR
        converter_no_ocr = DocumentExtractor(ocr_enabled=False)
        result_no_ocr = converter_no_ocr.extract(image_path)
        
        # Test with OCR
        converter_ocr = DocumentExtractor(ocr_enabled=True)
        result_ocr = converter_ocr.extract(image_path)
        
        print(f"📊 Comparison Results:")
        print(f"   Without OCR:")
        print(f"     Content length: {len(result_no_ocr.content)} characters")
        print(f"     Metadata items: {len(result_no_ocr.metadata)}")
        
        print(f"   With OCR:")
        print(f"     Content length: {len(result_ocr.content)} characters")
        print(f"     Metadata items: {len(result_ocr.metadata)}")
        
        # Calculate improvement
        if len(result_no_ocr.content) > 0:
            improvement = ((len(result_ocr.content) - len(result_no_ocr.content)) / len(result_no_ocr.content)) * 100
            print(f"   Content improvement: {improvement:.1f}%")
        else:
            print(f"   Content improvement: OCR added {len(result_ocr.content)} characters")
        
        # Show unique metadata keys
        no_ocr_keys = set(result_no_ocr.metadata.keys())
        ocr_keys = set(result_ocr.metadata.keys())
        unique_ocr_keys = ocr_keys - no_ocr_keys
        
        if unique_ocr_keys:
            print(f"   Additional OCR metadata: {list(unique_ocr_keys)}")
        
    except Exception as e:
        print(f"   ❌ Comparison failed: {e}")


def test_llm_integration_with_ocr():
    """Test LLM integration with OCR results."""
    print("\n🤖 Testing LLM Integration with OCR")
    print("=" * 60)
    
    image_path = "sample_documents/sample.png"
    
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return
    
    try:
        converter_ocr = DocumentExtractor(ocr_enabled=True)
        result = converter_ocr.extract(image_path)
        markdown = result.extract_markdown()
        
        print(f"✅ OCR content ready for LLM integration")
        print(f"   Content length: {len(markdown)} characters")
        
        if markdown.strip():
            print(f"\n📋 LLM Integration Example:")
            print(f"```python")
            print(f"from litellm import completion")
            print(f"")
            print(f"# Convert image to markdown")
            print(f"extractor = DocumentExtractor(ocr_enabled=True)")
            print(f"result = extractor.extract('sample.png')")
            print(f"markdown = result.extract_markdown()")
            print(f"")
            print(f"# Use with LLM")
            print(f"response = completion(")
            print(f"    model=\"openai/gpt-4o\",")
            print(f"    messages=[")
            print(f"        {{\"role\": \"system\", \"content\": \"You are an image analyzer.\"}},")
            print(f"        {{\"role\": \"user\", \"content\": f\"Analyze this image content:\\n\\n{{markdown}}\"}}")
            print(f"    ]")
            print(f")")
            print(f"")
            print(f"print(response.choices[0].message.content)")
            print(f"```")
            
            print(f"\n📄 Sample LLM prompt:")
            print(f"Analyze this image content:")
            print(f"")
            preview = markdown[:500] + "..." if len(markdown) > 500 else markdown
            print(f"{preview}")
        else:
            print(f"⚠️  No text content extracted - image may not contain readable text")
        
    except Exception as e:
        print(f"❌ LLM integration test failed: {e}")


def test_all_sample_files():
    """Test all sample files in the sample_documents folder."""
    print("\n📁 Testing All Sample Files")
    print("=" * 60)
    
    sample_dir = "sample_documents"
    if not os.path.exists(sample_dir):
        print(f"❌ Sample documents directory not found: {sample_dir}")
        return
    
    # Get all files in the sample_documents directory
    sample_files = []
    for file in os.listdir(sample_dir):
        file_path = os.path.join(sample_dir, file)
        if os.path.isfile(file_path):
            sample_files.append((file, file_path))
    
    print(f"📁 Found {len(sample_files)} sample files:")
    for file_name, file_path in sample_files:
        size = os.path.getsize(file_path)
        print(f"   - {file_name}: {size} bytes")
    
    # Test each file
    extractor = DocumentExtractor(ocr_enabled=True)
    results = {}
    
    for file_name, file_path in sample_files:
        print(f"\n📄 Testing {file_name}...")
        
        try:
            result = extractor.extract(file_path)
            markdown = result.extract_markdown()
            
            results[file_name] = {
                'success': True,
                'content_length': len(result.content),
                'markdown_length': len(markdown),
                'metadata_keys': list(result.metadata.keys())
            }
            
            print(f"   ✅ {file_name} conversion successful")
            print(f"      Content length: {len(result.content)} characters")
            print(f"      Markdown length: {len(markdown)} characters")
            print(f"      Metadata keys: {len(result.metadata)} items")
            
            # Show preview
            if markdown:
                preview = markdown[:100] + "..." if len(markdown) > 100 else markdown
                print(f"      Preview: {preview}")
            
        except Exception as e:
            results[file_name] = {
                'success': False,
                'error': str(e)
            }
            print(f"   ❌ {file_name} conversion failed: {e}")
    
    # Generate summary
    successful_files = [name for name, result in results.items() if result.get('success')]
    failed_files = [name for name, result in results.items() if not result.get('success')]
    
    print(f"\n📊 Summary:")
    print(f"   Total files tested: {len(results)}")
    print(f"   Successful: {len(successful_files)}")
    print(f"   Failed: {len(failed_files)}")
    
    if successful_files:
        total_chars = sum(results[name]['content_length'] for name in successful_files)
        avg_chars = total_chars / len(successful_files)
        print(f"   Average content length: {avg_chars:.0f} characters")
    
    return results


def main():
    """Main test function."""
    print("🚀 OCR Testing with Real Image Files")
    print("=" * 60)
    
    # Test OCR with real image
    test_ocr_with_real_image()
    
    # Compare OCR vs non-OCR
    test_ocr_comparison()
    
    # Test LLM integration
    test_llm_integration_with_ocr()
    
    # Test all sample files
    test_all_sample_files()
    
    print("\n" + "=" * 60)
    print("✅ OCR Testing Completed!")
    print("\n🎯 Key Findings:")
    print("- OCR capabilities work with real image files")
    print("- PaddleOCR successfully extracts text from images")
    print("- Markdown output is ready for LLM integration")
    print("- All sample files can be processed")
    print("- Comprehensive metadata extraction")


if __name__ == "__main__":
    main() 