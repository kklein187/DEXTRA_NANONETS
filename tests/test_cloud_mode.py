#!/usr/bin/env python3
"""
Comprehensive test script for cloud mode functionality.
Tests all documents in sample_documents/ with all output formats.
"""

import os
import json
import time
import traceback
from pathlib import Path
from docstrange import DocumentExtractor
from docstrange.exceptions import ConversionError


def get_file_size_mb(file_path):
    """Get file size in MB."""
    size_bytes = os.path.getsize(file_path)
    return round(size_bytes / (1024 * 1024), 2)


def test_document_conversion(extractor, file_path, output_format):
    """Test conversion of a single document to a specific format."""
    print(f"  📄 Testing {output_format.upper()} conversion...")
    
    try:
        # Convert document
        start_time = time.time()
        result = extractor.extract(file_path)
        conversion_time = time.time() - start_time
        
        # Get output based on format
        if output_format == "markdown":
            output = result.extract_markdown()
        elif output_format == "html":
            output = result.extract_html()
        elif output_format == "json":
            output = result.extract_data()
        elif output_format == "csv":
            output = result.extract_csv(include_all_tables=True)
        elif output_format == "text":
            output = result.extract_text()
        else:
            raise ValueError(f"Unknown output format: {output_format}")
        
        # Check if we got valid output
        if output and len(str(output).strip()) > 0:
            output_size = len(str(output)) if isinstance(output, str) else len(json.dumps(output))
            print(f"    ✅ Success! Output: {output_size} chars, Time: {conversion_time:.2f}s")
            
            # Show preview of output (first 200 chars)
            preview = str(output)[:200].replace('\n', ' ').strip()
            if len(preview) == 200:
                preview += "..."
            print(f"    📖 Preview: {preview}")
            
            return {
                "success": True,
                "output_size": output_size,
                "conversion_time": conversion_time,
                "preview": preview
            }
        else:
            print(f"    ⚠️  Empty output")
            return {"success": False, "error": "Empty output"}
            
    except ConversionError as e:
        if "Rate limit exceeded" in str(e):
            print(f"    🚫 Rate limited: {e}")
            return {"success": False, "error": "Rate limited", "rate_limited": True}
        else:
            print(f"    ❌ Conversion error: {e}")
            return {"success": False, "error": str(e)}
    except Exception as e:
        print(f"    ❌ Unexpected error: {e}")
        print(f"    📋 Traceback: {traceback.format_exc()}")
        return {"success": False, "error": str(e)}


def test_field_extraction(extractor, file_path):
    """Test field extraction functionality."""
    print(f"  🎯 Testing field extraction...")
    
    try:
        result = extractor.extract(file_path)
        
        # Test specified fields extraction
        fields_to_extract = ["title", "date", "total_amount", "vendor_name", "summary"]
        start_time = time.time()
        extracted = result.extract_data(specified_fields=fields_to_extract)
        extraction_time = time.time() - start_time
        
        if extracted and "extracted_fields" in extracted:
            extracted_count = len([v for v in extracted["extracted_fields"].values() if v is not None])
            print(f"    ✅ Field extraction success! {extracted_count}/{len(fields_to_extract)} fields found, Time: {extraction_time:.2f}s")
            print(f"    📊 Fields: {list(extracted['extracted_fields'].keys())}")
            return {
                "success": True,
                "fields_extracted": extracted_count,
                "total_fields": len(fields_to_extract),
                "extraction_time": extraction_time
            }
        else:
            print(f"    ⚠️  No fields extracted")
            return {"success": False, "error": "No fields extracted"}
            
    except ConversionError as e:
        if "Rate limit exceeded" in str(e):
            print(f"    🚫 Rate limited: {e}")
            return {"success": False, "error": "Rate limited", "rate_limited": True}
        else:
            print(f"    ❌ Field extraction error: {e}")
            return {"success": False, "error": str(e)}
    except Exception as e:
        print(f"    ❌ Unexpected error: {e}")
        return {"success": False, "error": str(e)}


def test_schema_extraction(extractor, file_path):
    """Test JSON schema extraction functionality."""
    print(f"  🏗️  Testing schema extraction...")
    
    try:
        result = extractor.extract(file_path)
        
        # Test with a simple schema
        schema = {
            "title": "string",
            "date": "string",
            "summary": "string",
            "key_points": ["string"],
            "metadata": {
                "page_count": "number",
                "language": "string"
            }
        }
        
        start_time = time.time()
        structured = result.extract_data(json_schema=schema)
        extraction_time = time.time() - start_time
        
        if structured and ("structured_data" in structured or "extracted_data" in structured):
            print(f"    ✅ Schema extraction success! Time: {extraction_time:.2f}s")
            return {
                "success": True,
                "extraction_time": extraction_time,
                "schema_used": schema
            }
        else:
            print(f"    ⚠️  No structured data extracted")
            return {"success": False, "error": "No structured data extracted"}
            
    except ConversionError as e:
        if "Rate limit exceeded" in str(e):
            print(f"    🚫 Rate limited: {e}")
            return {"success": False, "error": "Rate limited", "rate_limited": True}
        else:
            print(f"    ❌ Schema extraction error: {e}")
            return {"success": False, "error": str(e)}
    except Exception as e:
        print(f"    ❌ Unexpected error: {e}")
        return {"success": False, "error": str(e)}


def main():
    """Main test function."""
    print("🚀 Cloud Mode Comprehensive Test")
    print("=" * 50)
    
    # Initialize extractor in cloud mode (default)
    api_key = os.environ.get('NANONETS_API_KEY')
    if api_key:
        print("🔑 Using API key from environment for increased limits")
        extractor = DocumentExtractor(api_key=api_key)
    else:
        print("⚠️  No API key found - using rate-limited free tier")
        print("💡 Set NANONETS_API_KEY environment variable for increased limits")
        extractor = DocumentExtractor()
    
    print(f"🌐 Cloud mode: {extractor.cloud_mode}")
    print(f"🔑 Has API key: {bool(extractor.api_key)}")
    print()
    
    # Get sample documents
    sample_dir = Path("sample_documents")
    if not sample_dir.exists():
        print(f"❌ Sample documents directory not found: {sample_dir}")
        return
    
    # Get all files in sample_documents
    files = list(sample_dir.glob("*"))
    files = [f for f in files if f.is_file() and not f.name.startswith('.')]
    
    if not files:
        print(f"❌ No files found in {sample_dir}")
        return
    
    print(f"📁 Found {len(files)} test documents")
    for file in files:
        size_mb = get_file_size_mb(file)
        print(f"  📄 {file.name} ({size_mb} MB)")
    print()
    
    # Test formats
    output_formats = ["markdown", "html", "json", "csv", "text"]
    
    # Results tracking
    results = {}
    total_tests = 0
    successful_tests = 0
    rate_limited_count = 0
    
    # Test each document
    for file_path in files:
        file_name = file_path.name
        file_size = get_file_size_mb(file_path)
        
        print(f"🔍 Testing: {file_name} ({file_size} MB)")
        print("-" * 40)
        
        results[file_name] = {
            "file_size_mb": file_size,
            "formats": {},
            "field_extraction": {},
            "schema_extraction": {}
        }
        
        # Test all output formats
        for output_format in output_formats:
            total_tests += 1
            result = test_document_conversion(extractor, str(file_path), output_format)
            results[file_name]["formats"][output_format] = result
            
            if result["success"]:
                successful_tests += 1
            elif result.get("rate_limited"):
                rate_limited_count += 1
                
            # Add delay to avoid rate limiting
            time.sleep(0.5)
        
        # Test field extraction
        total_tests += 1
        field_result = test_field_extraction(extractor, str(file_path))
        results[file_name]["field_extraction"] = field_result
        if field_result["success"]:
            successful_tests += 1
        elif field_result.get("rate_limited"):
            rate_limited_count += 1
        
        time.sleep(0.5)
        
        # Test schema extraction
        total_tests += 1
        schema_result = test_schema_extraction(extractor, str(file_path))
        results[file_name]["schema_extraction"] = schema_result
        if schema_result["success"]:
            successful_tests += 1
        elif schema_result.get("rate_limited"):
            rate_limited_count += 1
        
        time.sleep(0.5)
        print()
    
    # Print summary
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"📁 Documents tested: {len(files)}")
    print(f"🧪 Total tests: {total_tests}")
    print(f"✅ Successful: {successful_tests}")
    print(f"❌ Failed: {total_tests - successful_tests - rate_limited_count}")
    print(f"🚫 Rate limited: {rate_limited_count}")
    print(f"📈 Success rate: {(successful_tests/total_tests)*100:.1f}%")
    
    if rate_limited_count > 0:
        print(f"\n💡 {rate_limited_count} tests were rate limited")
        print("   Get an API key from https://app.nanonets.com/#/keys for increased limits")
    
    print()
    
    # Print detailed results by document
    print("📋 DETAILED RESULTS")
    print("=" * 50)
    
    for file_name, file_results in results.items():
        print(f"\n📄 {file_name} ({file_results['file_size_mb']} MB):")
        
        # Format results
        format_success = sum(1 for r in file_results["formats"].values() if r["success"])
        print(f"  📑 Formats: {format_success}/{len(output_formats)} successful")
        
        for fmt, result in file_results["formats"].items():
            if result["success"]:
                print(f"    ✅ {fmt}: {result['output_size']} chars ({result['conversion_time']:.2f}s)")
            elif result.get("rate_limited"):
                print(f"    🚫 {fmt}: Rate limited")
            else:
                print(f"    ❌ {fmt}: {result['error']}")
        
        # Field extraction results
        field_result = file_results["field_extraction"]
        if field_result["success"]:
            print(f"  🎯 Field extraction: {field_result['fields_extracted']}/{field_result['total_fields']} fields ({field_result['extraction_time']:.2f}s)")
        elif field_result.get("rate_limited"):
            print(f"  🚫 Field extraction: Rate limited")
        else:
            print(f"  ❌ Field extraction: {field_result['error']}")
        
        # Schema extraction results
        schema_result = file_results["schema_extraction"]
        if schema_result["success"]:
            print(f"  🏗️  Schema extraction: Success ({schema_result['extraction_time']:.2f}s)")
        elif schema_result.get("rate_limited"):
            print(f"  🚫 Schema extraction: Rate limited")
        else:
            print(f"  ❌ Schema extraction: {schema_result['error']}")
    
    # Save results to JSON file
    results_file = "cloud_test_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "summary": {
                "documents_tested": len(files),
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests - rate_limited_count,
                "rate_limited": rate_limited_count,
                "success_rate": (successful_tests/total_tests)*100,
                "api_key_used": bool(extractor.api_key)
            },
            "detailed_results": results
        }, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    print("\n🎉 Cloud mode testing completed!")


if __name__ == "__main__":
    main() 