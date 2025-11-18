"""Conversion result class for handling different output formats."""

import csv
import io
import json
import logging
import re
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class MarkdownToJSONParser:
    """Comprehensive markdown to structured JSON parser."""
    
    def __init__(self):
        """Initialize the parser."""
        # Compile regex patterns for better performance
        self.header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        self.list_item_pattern = re.compile(r'^(\s*)[*\-+]\s+(.+)$', re.MULTILINE)
        self.ordered_list_pattern = re.compile(r'^(\s*)\d+\.\s+(.+)$', re.MULTILINE)
        self.code_block_pattern = re.compile(r'```(\w+)?\n(.*?)```', re.DOTALL)
        self.inline_code_pattern = re.compile(r'`([^`]+)`')
        self.link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        self.image_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
        self.table_pattern = re.compile(r'\|(.+)\|\s*\n\|[-\s|:]+\|\s*\n((?:\|.+\|\s*\n?)*)', re.MULTILINE)
        self.blockquote_pattern = re.compile(r'^>\s+(.+)$', re.MULTILINE)
        self.bold_pattern = re.compile(r'\*\*(.+?)\*\*')
        self.italic_pattern = re.compile(r'\*(.+?)\*')
        
    def parse(self, markdown_text: str) -> Dict[str, Any]:
        """Parse markdown text into structured JSON.
        
        Args:
            markdown_text: The markdown content to parse
            
        Returns:
            Structured JSON representation
        """
        if not markdown_text or not markdown_text.strip():
            return {
                "document": {
                    "sections": [], 
                    "metadata": {"total_sections": 0}
                }
            }
            
        lines = markdown_text.split('\n')
        sections = []
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.rstrip()
            
            # Check if this is a header
            header_match = self.header_pattern.match(line)
            if header_match:
                # Save previous section if exists
                if current_section is not None:
                    current_section['content'] = self._parse_content('\n'.join(current_content))
                    sections.append(current_section)
                
                # Start new section
                header_level = len(header_match.group(1))
                header_text = header_match.group(2).strip()
                
                current_section = {
                    "title": header_text,
                    "level": header_level,
                    "type": "section",
                    "content": {}
                }
                current_content = []
            else:
                # Add to current content
                if line.strip() or current_content:  # Keep empty lines only if we have content
                    current_content.append(line)
        
        # Don't forget the last section
        if current_section is not None:
            current_section['content'] = self._parse_content('\n'.join(current_content))
            sections.append(current_section)
        elif current_content:
            # Handle content without any headers
            sections.append({
                "title": "Content",
                "level": 1,
                "type": "section",
                "content": self._parse_content('\n'.join(current_content))
            })
        
        # Create hierarchical structure
        structured_sections = self._create_hierarchy(sections)
        
        return {
            "document": {
                "sections": structured_sections,
                "metadata": {
                    "total_sections": len(sections),
                    "max_heading_level": max([s.get('level', 1) for s in sections]) if sections else 0,
                    "has_tables": any('tables' in s.get('content', {}) for s in sections),
                    "has_code_blocks": any('code_blocks' in s.get('content', {}) for s in sections),
                    "has_lists": any('lists' in s.get('content', {}) for s in sections),
                    "has_images": any('images' in s.get('content', {}) for s in sections)
                }
            }
        }
    
    def _parse_content(self, content: str) -> Dict[str, Any]:
        """Parse content within a section into structured components."""
        if not content.strip():
            return {}
            
        result = {}
        
        # Extract and parse different content types
        paragraphs = self._extract_paragraphs(content)
        if paragraphs:
            result['paragraphs'] = paragraphs
            
        lists = self._extract_lists(content)
        if lists:
            result['lists'] = lists
            
        code_blocks = self._extract_code_blocks(content)
        if code_blocks:
            result['code_blocks'] = code_blocks
            
        tables = self._extract_tables(content)
        if tables:
            result['tables'] = tables
            
        images = self._extract_images(content)
        if images:
            result['images'] = images
            
        links = self._extract_links(content)
        if links:
            result['links'] = links
            
        blockquotes = self._extract_blockquotes(content)
        if blockquotes:
            result['blockquotes'] = blockquotes
        
        return result
    
    def _extract_paragraphs(self, content: str) -> List[str]:
        """Extract paragraphs from content."""
        # Remove code blocks, tables, lists, etc. to get clean paragraphs
        clean_content = content
        
        # Remove code blocks
        clean_content = self.code_block_pattern.sub('', clean_content)
        
        # Remove tables (simplified)
        clean_content = re.sub(r'\|.*\|', '', clean_content)
        
        # Remove list items
        clean_content = self.list_item_pattern.sub('', clean_content)
        clean_content = self.ordered_list_pattern.sub('', clean_content)
        
        # Remove blockquotes
        clean_content = self.blockquote_pattern.sub('', clean_content)
        
        # Split into paragraphs and clean
        paragraphs = []
        for para in clean_content.split('\n\n'):
            para = para.strip()
            if para and not para.startswith('#'):
                # Clean up markdown formatting for paragraphs
                para = self._clean_inline_formatting(para)
                paragraphs.append(para)
        
        return paragraphs
    
    def _extract_lists(self, content: str) -> List[Dict[str, Any]]:
        """Extract lists from content."""
        lists = []
        lines = content.split('\n')
        current_list = None
        
        for line in lines:
            line = line.rstrip()
            
            # Check for unordered list
            unordered_match = self.list_item_pattern.match(line)
            if unordered_match:
                indent_level = len(unordered_match.group(1)) // 2
                item_text = self._clean_inline_formatting(unordered_match.group(2))
                
                if current_list is None or current_list['type'] != 'unordered':
                    if current_list:
                        lists.append(current_list)
                    current_list = {'type': 'unordered', 'items': []}
                
                current_list['items'].append({
                    'text': item_text,
                    'level': indent_level
                })
                continue
            
            # Check for ordered list
            ordered_match = self.ordered_list_pattern.match(line)
            if ordered_match:
                indent_level = len(ordered_match.group(1)) // 2
                item_text = self._clean_inline_formatting(ordered_match.group(2))
                
                if current_list is None or current_list['type'] != 'ordered':
                    if current_list:
                        lists.append(current_list)
                    current_list = {'type': 'ordered', 'items': []}
                
                current_list['items'].append({
                    'text': item_text,
                    'level': indent_level
                })
                continue
            
            # If we hit a non-list line and have a current list, save it
            if current_list and line.strip():
                lists.append(current_list)
                current_list = None
        
        # Don't forget the last list
        if current_list:
            lists.append(current_list)
        
        return lists
    
    def _extract_code_blocks(self, content: str) -> List[Dict[str, str]]:
        """Extract code blocks from content."""
        code_blocks = []
        
        for match in self.code_block_pattern.finditer(content):
            language = match.group(1) or 'text'
            code = match.group(2).strip()
            
            code_blocks.append({
                'language': language,
                'code': code
            })
        
        return code_blocks
    
    def _extract_tables(self, content: str) -> List[Dict[str, Any]]:
        """Extract tables from content."""
        tables = []
        
        for match in self.table_pattern.finditer(content):
            header_row = match.group(1).strip()
            body_rows = match.group(2).strip()
            
            # Parse header
            headers = [cell.strip() for cell in header_row.split('|') if cell.strip()]
            
            # Parse body rows
            rows = []
            for row_line in body_rows.split('\n'):
                if row_line.strip() and '|' in row_line:
                    cells = [cell.strip() for cell in row_line.split('|') if cell.strip()]
                    if cells:
                        rows.append(cells)
            
            if headers and rows:
                tables.append({
                    'headers': headers,
                    'rows': rows,
                    'columns': len(headers)
                })
        
        return tables
    
    def _extract_images(self, content: str) -> List[Dict[str, str]]:
        """Extract images from content."""
        images = []
        
        for match in self.image_pattern.finditer(content):
            alt_text = match.group(1)
            url = match.group(2)
            
            images.append({
                'alt_text': alt_text,
                'url': url
            })
        
        return images
    
    def _extract_links(self, content: str) -> List[Dict[str, str]]:
        """Extract links from content."""
        links = []
        
        for match in self.link_pattern.finditer(content):
            text = match.group(1)
            url = match.group(2)
            
            links.append({
                'text': text,
                'url': url
            })
        
        return links
    
    def _extract_blockquotes(self, content: str) -> List[str]:
        """Extract blockquotes from content."""
        blockquotes = []
        
        for match in self.blockquote_pattern.finditer(content):
            quote_text = match.group(1).strip()
            blockquotes.append(quote_text)
        
        return blockquotes
    
    def _clean_inline_formatting(self, text: str) -> str:
        """Clean inline markdown formatting from text."""
        # Remove bold
        text = self.bold_pattern.sub(r'\1', text)
        # Remove italic
        text = self.italic_pattern.sub(r'\1', text)
        # Remove inline code
        text = self.inline_code_pattern.sub(r'\1', text)
        
        return text.strip()
    
    def _create_hierarchy(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create hierarchical structure from flat sections list."""
        if not sections:
            return []
        
        result = []
        stack = []
        
        for section in sections:
            level = section['level']
            
            # Pop from stack until we find a parent at appropriate level
            while stack and stack[-1]['level'] >= level:
                stack.pop()
            
            # If we have a parent, add this section as a subsection
            if stack:
                parent = stack[-1]
                if 'subsections' not in parent:
                    parent['subsections'] = []
                parent['subsections'].append(section)
            else:
                # This is a top-level section
                result.append(section)
            
            # Add this section to the stack
            stack.append(section)
        
        return result


class MarkdownToHTMLConverter:
    """Comprehensive markdown to HTML extractor."""
    
    def __init__(self):
        """Initialize the extractor."""
        # Compile regex patterns for better performance
        self.header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        self.bold_pattern = re.compile(r'\*\*(.+?)\*\*')
        self.italic_pattern = re.compile(r'\*(.+?)\*')
        self.bold_italic_pattern = re.compile(r'\*\*\*(.+?)\*\*\*')
        self.strikethrough_pattern = re.compile(r'~~(.+?)~~')
        self.inline_code_pattern = re.compile(r'`([^`]+)`')
        self.link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        self.image_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
        self.horizontal_rule_pattern = re.compile(r'^---+$', re.MULTILINE)
        self.blockquote_pattern = re.compile(r'^>\s+(.+)$', re.MULTILINE)
        
    def extract(self, markdown_text: str) -> str:
        """Convert markdown text to HTML.
        
        Args:
            markdown_text: The markdown content to extract
            
        Returns:
            HTML string
        """
        html = markdown_text
        
        # Process code blocks first (before other inline processing)
        html = self._process_code_blocks(html)
        
        # Process tables
        html = self._process_tables(html)
        
        # Process horizontal rules
        html = self._process_horizontal_rules(html)
        
        # Process blockquotes
        html = self._process_blockquotes(html)
        
        # Process headers
        html = self._process_headers(html)
        
        # Process lists
        html = self._process_lists(html)
        
        # Process inline elements
        html = self._process_inline_elements(html)
        
        # Process paragraphs
        html = self._process_paragraphs(html)
        
        return html
    
    def _process_code_blocks(self, text: str) -> str:
        """Process fenced code blocks."""
        # Handle ```code blocks```
        def replace_code_block(match):
            language = match.group(1) or ''
            code = match.group(2)
            lang_class = f' class="language-{language}"' if language else ''
            return f'<pre><code{lang_class}>{self._escape_html(code)}</code></pre>'
        
        text = re.sub(r'```(\w+)?\n(.*?)\n```', replace_code_block, text, flags=re.DOTALL)
        
        # Handle indented code blocks (4 spaces or tab)
        lines = text.split('\n')
        in_code_block = False
        code_lines = []
        result_lines = []
        
        for line in lines:
            if line.startswith('    ') or line.startswith('\t'):
                if not in_code_block:
                    in_code_block = True
                    code_lines = [line.lstrip()]
                else:
                    code_lines.append(line.lstrip())
            else:
                if in_code_block:
                    # End code block
                    code_content = '\n'.join(code_lines)
                    result_lines.append(f'<pre><code>{self._escape_html(code_content)}</code></pre>')
                    code_lines = []
                    in_code_block = False
                result_lines.append(line)
        
        if in_code_block:
            code_content = '\n'.join(code_lines)
            result_lines.append(f'<pre><code>{self._escape_html(code_content)}</code></pre>')
        
        return '\n'.join(result_lines)
    
    def _process_tables(self, text: str) -> str:
        """Process markdown tables."""
        lines = text.split('\n')
        result_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this line looks like a table header
            if '|' in line and i + 1 < len(lines) and '|' in lines[i + 1]:
                # Check if next line is separator
                next_line = lines[i + 1]
                if re.match(r'^\s*\|[\s\-:|]+\|\s*$', next_line):
                    # This is a table
                    table_lines = [line]
                    j = i + 1
                    
                    # Collect all table rows
                    while j < len(lines) and '|' in lines[j]:
                        table_lines.append(lines[j])
                        j += 1
                    
                    # Convert table to HTML
                    html_table = self._convert_table_to_html(table_lines)
                    result_lines.append(html_table)
                    i = j
                    continue
            
            result_lines.append(line)
            i += 1
        
        return '\n'.join(result_lines)
    
    def _convert_table_to_html(self, table_lines: List[str]) -> str:
        """Convert table lines to HTML table."""
        if len(table_lines) < 2:
            return table_lines[0] if table_lines else ''
        
        html_parts = ['<table>']
        
        # Process header
        header_cells = [cell.strip() for cell in table_lines[0].split('|')[1:-1]]
        html_parts.append('<thead><tr>')
        for cell in header_cells:
            html_parts.append(f'<th>{self._escape_html(cell)}</th>')
        html_parts.append('</tr></thead>')
        
        # Process body (skip separator line)
        html_parts.append('<tbody>')
        for line in table_lines[2:]:
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            html_parts.append('<tr>')
            for cell in cells:
                html_parts.append(f'<td>{self._escape_html(cell)}</td>')
            html_parts.append('</tr>')
        html_parts.append('</tbody>')
        
        html_parts.append('</table>')
        return '\n'.join(html_parts)
    
    def _process_horizontal_rules(self, text: str) -> str:
        """Process horizontal rules."""
        return self.horizontal_rule_pattern.sub('<hr>', text)
    
    def _process_blockquotes(self, text: str) -> str:
        """Process blockquotes."""
        lines = text.split('\n')
        result_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            if line.startswith('> '):
                # Start blockquote
                quote_lines = [line[2:]]  # Remove '> '
                j = i + 1
                
                # Collect all quote lines
                while j < len(lines) and (lines[j].startswith('> ') or lines[j].strip() == ''):
                    if lines[j].startswith('> '):
                        quote_lines.append(lines[j][2:])
                    else:
                        quote_lines.append('')
                    j += 1
                
                # Convert to HTML
                quote_content = '\n'.join(quote_lines)
                quote_html = self._process_inline_elements(quote_content)
                result_lines.append(f'<blockquote>{quote_html}</blockquote>')
                i = j
                continue
            
            result_lines.append(line)
            i += 1
        
        return '\n'.join(result_lines)
    
    def _process_headers(self, text: str) -> str:
        """Process markdown headers."""
        def replace_header(match):
            level = len(match.group(1))
            content = match.group(2)
            return f'<h{level}>{self._escape_html(content)}</h{level}>'
        
        return self.header_pattern.sub(replace_header, text)
    
    def _process_lists(self, text: str) -> str:
        """Process ordered and unordered lists."""
        lines = text.split('\n')
        result_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for unordered list
            if re.match(r'^[\s]*[-*+]\s+', line):
                list_lines = self._collect_list_items(lines, i, r'^[\s]*[-*+]\s+')
                html_list = self._convert_list_to_html(list_lines, 'ul')
                result_lines.append(html_list)
                i += len(list_lines)
                continue
            
            # Check for ordered list
            elif re.match(r'^[\s]*\d+\.\s+', line):
                list_lines = self._collect_list_items(lines, i, r'^[\s]*\d+\.\s+')
                html_list = self._convert_list_to_html(list_lines, 'ol')
                result_lines.append(html_list)
                i += len(list_lines)
                continue
            
            result_lines.append(line)
            i += 1
        
        return '\n'.join(result_lines)
    
    def _collect_list_items(self, lines: List[str], start_idx: int, pattern: str) -> List[str]:
        """Collect consecutive list items."""
        items = []
        i = start_idx
        
        while i < len(lines):
            line = lines[i]
            if re.match(pattern, line):
                items.append(line)
                i += 1
            elif line.strip() == '':
                # Empty line might be part of list item
                items.append(line)
                i += 1
            else:
                break
        
        return items
    
    def _convert_list_to_html(self, list_lines: List[str], list_type: str) -> str:
        """Convert list lines to HTML list."""
        html_parts = [f'<{list_type}>']
        
        for line in list_lines:
            if line.strip() == '':
                continue
            
            # Extract list item content
            if list_type == 'ul':
                content = re.sub(r'^[\s]*[-*+]\s+', '', line)
            else:
                content = re.sub(r'^[\s]*\d+\.\s+', '', line)
            
            # Process inline elements in list item
            content = self._process_inline_elements(content)
            html_parts.append(f'<li>{content}</li>')
        
        html_parts.append(f'</{list_type}>')
        return '\n'.join(html_parts)
    
    def _process_inline_elements(self, text: str) -> str:
        """Process inline markdown elements."""
        # Process bold and italic (order matters)
        text = self.bold_italic_pattern.sub(r'<strong><em>\1</em></strong>', text)
        text = self.bold_pattern.sub(r'<strong>\1</strong>', text)
        text = self.italic_pattern.sub(r'<em>\1</em>', text)
        
        # Process strikethrough
        text = self.strikethrough_pattern.sub(r'<del>\1</del>', text)
        
        # Process inline code
        text = self.inline_code_pattern.sub(r'<code>\1</code>', text)
        
        # Process links
        text = self.link_pattern.sub(r'<a href="\2">\1</a>', text)
        
        # Process images
        text = self.image_pattern.sub(r'<img src="\2" alt="\1">', text)
        
        return text
    
    def _process_paragraphs(self, text: str) -> str:
        """Process paragraphs by wrapping non-empty lines in <p> tags."""
        lines = text.split('\n')
        result_lines = []
        current_paragraph = []
        
        for line in lines:
            if line.strip() == '':
                if current_paragraph:
                    # End current paragraph
                    paragraph_content = ' '.join(current_paragraph)
                    result_lines.append(f'<p>{paragraph_content}</p>')
                    current_paragraph = []
            else:
                # Check if line is already an HTML block element
                if re.match(r'^<(h[1-6]|p|div|blockquote|pre|table|ul|ol|li|hr)', line.strip()):
                    # Flush current paragraph if any
                    if current_paragraph:
                        paragraph_content = ' '.join(current_paragraph)
                        result_lines.append(f'<p>{paragraph_content}</p>')
                        current_paragraph = []
                    result_lines.append(line)
                else:
                    current_paragraph.append(line)
        
        # Handle any remaining paragraph
        if current_paragraph:
            paragraph_content = ' '.join(current_paragraph)
            result_lines.append(f'<p>{paragraph_content}</p>')
        
        return '\n'.join(result_lines)
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#39;'))


class ConversionResult:
    """Result object with methods to export to different formats."""
    
    def __init__(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Initialize the conversion result.
        
        Args:
            content: The converted content as string
            metadata: Optional metadata about the conversion
        """
        self.content = content
        self.metadata = metadata or {}
        self._html_converter = MarkdownToHTMLConverter()
        self._json_parser = MarkdownToJSONParser()
    
    def extract_markdown(self) -> str:
        """Export as markdown.
        
        Returns:
            The content formatted as markdown
        """
        return self.content
    
    def extract_html(self) -> str:
        """Export as HTML.
        
        Returns:
            The content formatted as HTML
        """
        # Convert markdown content to HTML using the comprehensive extractor
        html_content = self._html_converter.extract(self.content)
        
        # Wrap in HTML structure with Nanonets design system
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Converted Document</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #1F2129;
            background-color: #FFFFFF;
            margin: 0;
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .content {{
            background: #FFFFFF;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        
        /* Typography */
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Inter', sans-serif;
            color: #1D2554;
            margin-top: 2rem;
            margin-bottom: 1rem;
            font-weight: 600;
            line-height: 1.3;
        }}
        
        h1 {{ font-size: 48px; letter-spacing: -0.02em; margin-top: 0; }}
        h2 {{ font-size: 36px; letter-spacing: -0.01em; }}
        h3 {{ font-size: 24px; }}
        h4 {{ font-size: 20px; }}
        h5 {{ font-size: 16px; }}
        h6 {{ font-size: 14px; }}
        
        p {{
            font-size: 16px;
            line-height: 1.6;
            margin-bottom: 1rem;
            color: #1F2129;
        }}
        
        /* Lists */
        ul, ol {{
            margin: 1rem 0;
            padding-left: 2rem;
        }}
        
        li {{
            margin-bottom: 0.5rem;
            line-height: 1.6;
        }}
        
        /* Code */
        code {{
            background-color: #F8FAFF;
            color: #3A4DB2;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
            font-size: 0.9em;
            border: 1px solid #EAEDFF;
        }}
        
        pre {{
            background-color: #F8FAFF;
            border: 1px solid #EAEDFF;
            border-radius: 8px;
            padding: 1.5rem;
            overflow-x: auto;
            margin: 1.5rem 0;
        }}
        
        pre code {{
            background: none;
            border: none;
            padding: 0;
            color: #1F2129;
        }}
        
        /* Tables */
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1.5rem 0;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        
        th, td {{
            border: 1px solid #EAEDFF;
            padding: 0.75rem;
            text-align: left;
            vertical-align: top;
        }}
        
        th {{
            background-color: #F2F4FF;
            color: #1D2554;
            font-weight: 600;
            font-size: 14px;
        }}
        
        td {{
            background-color: #FFFFFF;
            font-size: 14px;
        }}
        
        tr:nth-child(even) td {{
            background-color: #F8FAFF;
        }}
        
        /* Links */
        a {{
            color: #546FFF;
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: border-bottom-color 0.2s ease;
        }}
        
        a:hover {{
            border-bottom-color: #546FFF;
        }}
        
        /* Images */
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 1rem 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}
        
        /* Blockquotes */
        blockquote {{
            border-left: 4px solid #546FFF;
            margin: 1.5rem 0;
            padding: 1rem 1.5rem;
            background-color: #F8FAFF;
            border-radius: 0 8px 8px 0;
            font-style: italic;
        }}
        
        blockquote p {{
            margin: 0;
            color: #3A4DB2;
        }}
        
        /* Horizontal rules */
        hr {{
            border: none;
            height: 1px;
            background-color: #EAEDFF;
            margin: 2rem 0;
        }}
        
        /* Emphasis */
        strong {{
            font-weight: 600;
            color: #1D2554;
        }}
        
        em {{
            font-style: italic;
            color: #3A4DB2;
        }}
        
        del {{
            text-decoration: line-through;
            color: #676767;
        }}
        
        /* Responsive design */
        @media (max-width: 768px) {{
            body {{
                padding: 1rem;
            }}
            
            .content {{
                padding: 1rem;
            }}
            
            h1 {{ font-size: 32px; }}
            h2 {{ font-size: 28px; }}
            h3 {{ font-size: 20px; }}
            
            table {{
                font-size: 12px;
            }}
            
            th, td {{
                padding: 0.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="content">
        {html_content}
    </div>
</body>
</html>"""
    
    def extract_data(self, specified_fields: Optional[list] = None, json_schema: Optional[dict] = None, 
                ollama_url: str = "http://localhost:11434", ollama_model: str = "llama3.2") -> Dict[str, Any]:
        """Convert content to JSON format.
        
        Args:
            specified_fields: List of specific fields to extract (uses Ollama)
            json_schema: JSON schema to conform to (uses Ollama)
            ollama_url: Ollama server URL for local processing
            ollama_model: Model name for local processing
            
        Returns:
            Dictionary containing the JSON representation
        """
        try:
            # If specific fields or schema are requested, use Ollama extraction
            if specified_fields or json_schema:
                try:
                    from docstrange.services import OllamaFieldExtractor
                    extractor = OllamaFieldExtractor(base_url=ollama_url, model=ollama_model)
                    
                    if extractor.is_available():
                        if specified_fields:
                            extracted_data = extractor.extract_fields(self.content, specified_fields)
                            return {
                                "extracted_fields": extracted_data,
                                "requested_fields": specified_fields,
                                **self.metadata,
                                "format": "local_specified_fields",
                                "extractor": "ollama"
                            }
                        elif json_schema:
                            extracted_data = extractor.extract_with_schema(self.content, json_schema)
                            return {
                                "extracted_data": extracted_data,
                                "schema": json_schema,
                                **self.metadata,
                                "format": "local_json_schema", 
                                "extractor": "ollama"
                            }
                    else:
                        logger.warning("Ollama not available for field extraction, falling back to standard parsing")
                except Exception as e:
                    logger.warning(f"Ollama extraction failed: {e}, falling back to standard parsing")
            
            # For general JSON conversion, try Ollama first for better document understanding
            try:
                from docstrange.services import OllamaFieldExtractor
                extractor = OllamaFieldExtractor(base_url=ollama_url, model=ollama_model)
                
                if extractor.is_available():
                    # Ask Ollama to extract the entire document to structured JSON
                    document_json = extractor.extract_document_json(self.content)
                    return {
                        **document_json,
                        **self.metadata,
                        "format": "ollama_structured_json",
                        "extractor": "ollama"
                    }
                else:
                    logger.info("Ollama not available, using fallback JSON parser")
            except Exception as e:
                logger.warning(f"Ollama document conversion failed: {e}, using fallback parser")
            
            # Fallback to original parsing logic
            parsed_content = self._json_parser.parse(self.content)
            return {
                **parsed_content,
                **self.metadata,
                "format": "structured_json"
            }
            
        except Exception as e:
            logger.error(f"JSON conversion failed: {e}")
            return {
                "error": f"Failed to extract to JSON: {str(e)}",
                "raw_content": self.content,
                **self.metadata,
                "format": "error"
            }
    
    def extract_text(self) -> str:
        """Export as plain text.
        
        Returns:
            The content as plain text
        """
        return self.content
    
    def extract_csv(self, table_index: int = 0, include_all_tables: bool = False) -> str:
        """Export tables as CSV format.
        
        Args:
            table_index: Which table to export (0-based index). Default is 0 (first table).
            include_all_tables: If True, export all tables with separators. Default is False.
        
        Returns:
            CSV formatted string of the table(s)
        
        Raises:
            ValueError: If no tables are found or table_index is out of range
        """
        # Parse the content to extract tables
        json_data = self.extract_data()
        
        # Extract all tables from all sections
        tables = []
        
        def extract_tables_from_sections(sections):
            for section in sections:
                content = section.get('content', {})
                if 'tables' in content:
                    tables.extend(content['tables'])
                # Recursively check subsections
                if 'subsections' in section:
                    extract_tables_from_sections(section['subsections'])
        
        if 'document' in json_data and 'sections' in json_data['document']:
            extract_tables_from_sections(json_data['document']['sections'])
        
        if not tables:
            # If no structured tables found, try to parse markdown tables directly
            tables = self._extract_markdown_tables_directly(self.content)
        
        if not tables:
            raise ValueError("No tables found in the document content")
        
        if include_all_tables:
            # Export all tables with separators
            csv_output = io.StringIO()
            writer = csv.writer(csv_output)
            
            for i, table in enumerate(tables):
                if i > 0:
                    # Add separator between tables
                    writer.writerow([])
                    writer.writerow([f"=== Table {i + 1} ==="])
                    writer.writerow([])
                
                # Write table headers if available
                if 'headers' in table and table['headers']:
                    writer.writerow(table['headers'])
                
                # Write table rows
                if 'rows' in table:
                    for row in table['rows']:
                        writer.writerow(row)
            
            return csv_output.getvalue()
        else:
            # Export specific table
            if table_index >= len(tables):
                raise ValueError(f"Table index {table_index} out of range. Found {len(tables)} table(s)")
            
            table = tables[table_index]
            csv_output = io.StringIO()
            writer = csv.writer(csv_output)
            
            # Write table headers if available
            if 'headers' in table and table['headers']:
                writer.writerow(table['headers'])
            
            # Write table rows
            if 'rows' in table:
                for row in table['rows']:
                    writer.writerow(row)
            
            return csv_output.getvalue()
    
    def _extract_markdown_tables_directly(self, content: str) -> List[Dict[str, Any]]:
        """Extract tables directly from markdown content as fallback."""
        tables = []
        table_pattern = re.compile(r'\|(.+)\|\s*\n\|[-\s|:]+\|\s*\n((?:\|.+\|\s*\n?)*)', re.MULTILINE)
        
        for match in table_pattern.finditer(content):
            header_row = match.group(1).strip()
            body_rows = match.group(2).strip()
            
            # Parse header
            headers = [cell.strip() for cell in header_row.split('|') if cell.strip()]
            
            # Parse body rows
            rows = []
            for row_line in body_rows.split('\n'):
                if row_line.strip() and '|' in row_line:
                    cells = [cell.strip() for cell in row_line.split('|') if cell.strip()]
                    if cells:
                        rows.append(cells)
            
            if headers and rows:
                tables.append({
                    'headers': headers,
                    'rows': rows,
                    'columns': len(headers)
                })
        
        return tables
    
    def __str__(self) -> str:
        """String representation of the result."""
        return self.content
    
    def __repr__(self) -> str:
        """Representation of the result object."""
        return f"ConversionResult(content='{self.content[:50]}...', metadata={self.metadata})" 