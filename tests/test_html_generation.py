#!/usr/bin/env python3
"""Test script for the improved HTML generation."""

from docstrange.result import ConversionResult

def test_html_generation():
    """Test the HTML generation with various markdown elements."""
    
    # Sample markdown content with various elements
    markdown_content = """# Main Title

## Subtitle

This is a **bold** paragraph with *italic* text and `inline code`. You can also have ***bold italic*** text and ~~strikethrough~~ text.

### Lists

#### Unordered List
- Item 1
- Item 2 with **bold text**
- Item 3 with `code`

#### Ordered List
1. First item
2. Second item
3. Third item

### Code Blocks

#### Fenced Code Block
```python
def hello_world():
    print("Hello, World!")
    return True
```

#### Indented Code Block
    def another_function():
        return "This is indented code"

### Tables

| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| **Bold** | *Italic* | `Code`   |

### Links and Images

Here's a [link to Google](https://www.google.com) and an image:

![Sample Image](https://via.placeholder.com/300x200)

### Blockquotes

> This is a blockquote with **bold text** and `code`.
> 
> It can span multiple lines.

### Horizontal Rules

---

### Mixed Content

Here's a paragraph with:
- **Bold text**
- *Italic text*
- `Inline code`
- [A link](https://example.com)

And some code:

```javascript
function greet(name) {
    return `Hello, ${name}!`;
}
```

### Nested Elements

1. **Bold item** with *italic* text
2. Item with `code` and [link](https://example.com)
3. Item with:
   - Nested list item
   - Another nested item

> **Bold quote** with *italic* and `code`
> 
> - List in quote
> - Another item

---

Final paragraph with all elements: **bold**, *italic*, `code`, [link](https://example.com), and ~~strikethrough~~.
"""

    # Create conversion result
    result = ConversionResult(markdown_content)
    
    # Generate HTML
    html_output = result.extract_html()
    
    # Save to file for inspection
    with open('test_output.html', 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    print("✅ HTML generation test completed!")
    print("📄 Output saved to 'test_output.html'")
    print("🌐 Open the file in a browser to see the result")
    
    # Print a snippet of the generated HTML
    print("\n📋 HTML snippet (first 500 characters):")
    print(html_output[:500] + "...")

if __name__ == "__main__":
    test_html_generation() 