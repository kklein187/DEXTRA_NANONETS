#!/usr/bin/env python3
"""Test the enhanced JSON structure parsing functionality."""

import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from docstrange.result import ConversionResult

def test_basic_structure():
    """Test basic markdown structure parsing."""
    markdown_content = """# Main Title

This is a paragraph under the main title.

## Section 1

Here's some content in section 1.

### Subsection 1.1

More content here.

## Section 2

Another section with content.
"""
    
    result = ConversionResult(markdown_content, {"source": "test"})
    json_data = result.extract_data()
    
    print("=== Basic Structure Test ===")
    print(json.dumps(json_data, indent=2))
    
    # Verify structure
    assert "document" in json_data
    assert "sections" in json_data["document"]
    assert len(json_data["document"]["sections"]) == 1  # Main Title
    
    main_section = json_data["document"]["sections"][0]
    assert main_section["title"] == "Main Title"
    assert main_section["level"] == 1
    assert "subsections" in main_section
    assert len(main_section["subsections"]) == 2  # Section 1 and 2
    
    print("✓ Basic structure test passed\n")

def test_content_types():
    """Test different content types parsing."""
    markdown_content = """# Content Types Demo

## Lists Section

Here are some lists:

- Item 1
- Item 2
  - Nested item
- Item 3

1. First ordered item
2. Second ordered item
3. Third ordered item

## Code Section

Here's some code:

```python
def hello_world():
    print("Hello, World!")
```

```javascript
function greet(name) {
    console.log(`Hello, ${name}!`);
}
```

## Table Section

| Name | Age | City |
|------|-----|------|
| John | 30  | NYC  |
| Jane | 25  | LA   |

## Links and Images

Visit [OpenAI](https://openai.com) for more info.

![Sample Image](https://example.com/image.jpg)

## Quotes

> This is a blockquote
> with multiple lines.
"""
    
    result = ConversionResult(markdown_content, {"source": "comprehensive_test"})
    json_data = result.extract_data()
    
    print("=== Content Types Test ===")
    print(json.dumps(json_data, indent=2))
    
    # Verify metadata
    metadata = json_data["document"]["metadata"]
    assert metadata["has_lists"] == True
    assert metadata["has_code_blocks"] == True
    assert metadata["has_tables"] == True
    assert metadata["has_images"] == True
    
    # Find the lists section
    lists_section = None
    for section in json_data["document"]["sections"][0]["subsections"]:
        if section["title"] == "Lists Section":
            lists_section = section
            break
    
    assert lists_section is not None
    assert "lists" in lists_section["content"]
    assert len(lists_section["content"]["lists"]) == 2  # unordered and ordered
    
    # Find the code section
    code_section = None
    for section in json_data["document"]["sections"][0]["subsections"]:
        if section["title"] == "Code Section":
            code_section = section
            break
    
    assert code_section is not None
    assert "code_blocks" in code_section["content"]
    assert len(code_section["content"]["code_blocks"]) == 2
    assert code_section["content"]["code_blocks"][0]["language"] == "python"
    
    print("✓ Content types test passed\n")

def test_no_headers():
    """Test content without headers."""
    markdown_content = """This is just plain content.

- Item 1
- Item 2

Some more text here."""
    
    result = ConversionResult(markdown_content)
    json_data = result.extract_data()
    
    print("=== No Headers Test ===")
    print(json.dumps(json_data, indent=2))
    
    # Should create a default "Content" section
    assert len(json_data["document"]["sections"]) == 1
    assert json_data["document"]["sections"][0]["title"] == "Content"
    assert json_data["document"]["sections"][0]["level"] == 1
    
    print("✓ No headers test passed\n")

def test_empty_content():
    """Test empty or whitespace-only content."""
    result = ConversionResult("   \n\n   ")
    json_data = result.extract_data()
    
    print("=== Empty Content Test ===")
    print(json.dumps(json_data, indent=2))
    
    # Should return minimal structure
    assert json_data["document"]["sections"] == []
    assert json_data["document"]["metadata"]["total_sections"] == 0
    
    print("✓ Empty content test passed\n")

def test_complex_hierarchy():
    """Test complex heading hierarchy."""
    markdown_content = """# Level 1

Content for level 1.

## Level 2A

Content for 2A.

### Level 3A

Content for 3A.

#### Level 4A

Content for 4A.

### Level 3B

Content for 3B.

## Level 2B

Content for 2B.

# Another Level 1

More top-level content.
"""
    
    result = ConversionResult(markdown_content)
    json_data = result.extract_data()
    
    print("=== Complex Hierarchy Test ===")
    print(json.dumps(json_data, indent=2))
    
    # Should have 2 top-level sections
    assert len(json_data["document"]["sections"]) == 2
    
    # First section should have subsections
    first_section = json_data["document"]["sections"][0]
    assert first_section["title"] == "Level 1"
    assert "subsections" in first_section
    assert len(first_section["subsections"]) == 2  # 2A and 2B
    
    # Check nested structure
    level_2a = first_section["subsections"][0]
    assert level_2a["title"] == "Level 2A"
    assert "subsections" in level_2a
    assert len(level_2a["subsections"]) == 2  # 3A and 3B
    
    print("✓ Complex hierarchy test passed\n")

def main():
    """Run all tests."""
    print("Testing Enhanced JSON Structure Parsing\n")
    
    test_basic_structure()
    test_content_types()
    test_no_headers()
    test_empty_content()
    test_complex_hierarchy()
    
    print("🎉 All tests passed!")

if __name__ == "__main__":
    main() 