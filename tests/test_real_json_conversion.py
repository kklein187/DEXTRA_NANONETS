#!/usr/bin/env python3
"""Test real document to structured JSON conversion."""

import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from docstrange import DocumentExtractor

def test_markdown_to_json():
    """Test converting a markdown string to structured JSON."""
    # Create some sample markdown content
    sample_markdown = """# Document Analysis Report

This document provides a comprehensive analysis of the data processing pipeline.

## Executive Summary

The analysis reveals several key findings that impact our current operations.

### Key Metrics

Our performance indicators show:

- **Processing Speed**: 95% improvement
- **Accuracy Rate**: 99.7%
- **Error Reduction**: 85% decrease

## Technical Implementation

### Architecture Overview

The system consists of multiple components:

1. Data ingestion layer
2. Processing engine
3. Output formatter
4. Quality assurance module

### Code Examples

Here's the main processing function:

```python
def process_document(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Process the content
    result = analyze_content(content)
    return result
```

### Performance Metrics

| Component | Before | After | Improvement |
|-----------|--------|-------|-------------|
| Ingestion | 5 sec  | 1 sec | 80%         |
| Processing| 10 sec | 2 sec | 80%         |
| Output    | 3 sec  | 1 sec | 67%         |

## Recommendations

> Based on our analysis, we recommend the following actions:

1. Continue with current optimization strategies
2. Implement additional monitoring
3. Scale the infrastructure

### Next Steps

For more information, visit our [documentation](https://example.com/docs).

![Performance Chart](https://example.com/chart.png)

## Conclusion

The implementation has exceeded expectations and provides a solid foundation for future development.
"""

    # Create a extractor and extract the markdown
    extractor = DocumentExtractor()
    result = extractor._processors['txt'].process(sample_markdown, {})
    
    # Export as structured JSON
    json_data = result.extract_data()
    
    print("=== Structured JSON Output ===")
    print(json.dumps(json_data, indent=2))
    
    # Verify the structure
    assert "document" in json_data
    assert "sections" in json_data["document"]
    
    # Should have main sections
    sections = json_data["document"]["sections"]
    assert len(sections) > 0
    
    # Find the main title
    main_section = sections[0]
    assert main_section["title"] == "Document Analysis Report"
    assert main_section["level"] == 1
    
    # Verify metadata
    metadata = json_data["document"]["metadata"]
    assert metadata["has_tables"] == True
    assert metadata["has_code_blocks"] == True
    assert metadata["has_lists"] == True
    assert metadata["has_images"] == True
    
    print("\n✓ Real document conversion test passed!")
    
    # Save the output for inspection
    with open('tests/sample_structured_output.json', 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print("✓ Structured JSON saved to tests/sample_structured_output.json")

def main():
    """Run the test."""
    print("Testing Real Document to Structured JSON Conversion\n")
    test_markdown_to_json()
    print("\n🎉 Test completed successfully!")

if __name__ == "__main__":
    main() 