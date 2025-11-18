# Docstrange MCP Server (Local Development Only)

This MCP (Model Context Protocol) server enables Claude Code to interact with PDF documents through your docstrange library, providing powerful document navigation and search capabilities with intelligent token-aware processing.

> **Important**: This MCP server is designed for local development and is **not distributed** with the PyPI package. You must clone the repository to use it.

## Features

### Basic Tools
1. **parse_pdf** - Parse a PDF file and convert it to markdown format
2. **get_headers** - Get all headers/sections from a parsed document
3. **search_document** - Search for keywords or phrases in the document
4. **get_section** - Get the content of a specific section by title
5. **get_section_summaries** - Get summaries of all sections in the document
6. **get_full_content** - Get the full markdown content of the document
7. **list_cached_documents** - List all documents currently cached in memory

### Intelligent Features

#### 1. Token-Aware Processing
The server counts tokens for every section and the entire document, providing smart recommendations for how to process documents based on their size.

#### 2. Hierarchical Navigation
Documents are parsed into a tree structure, allowing navigation through parent-child relationships between sections.

#### 3. Smart Chunking
Documents can be automatically divided into chunks that fit within specified token limits.

### Advanced Tools

#### `get_document_info`
Returns comprehensive document metadata including:
- Total token count
- Token distribution across sections
- Processing recommendations based on size
- Suggested chunk count

Example response:
```json
{
  "total_tokens": 45000,
  "total_sections": 23,
  "token_distribution": {
    "min": 150,
    "max": 5000,
    "avg": 1956
  },
  "processing_recommendation": {
    "approach": "chunked_processing",
    "reason": "Document fits in large context but benefits from chunking (45000 tokens)",
    "strategy": "Use hierarchical navigation and chunk processing"
  },
  "suggested_chunk_count": 12
}
```

#### `get_hierarchical_structure`
Returns the document's tree structure showing parent-child relationships between sections.

#### `get_section_chunks`
Divides the document into chunks that fit within a token limit.

Parameters:
- `file_path`: Path to the document
- `max_tokens`: Maximum tokens per chunk (default: 4000)

#### `get_chunk_content`
Retrieves the actual content of a specific chunk.

Parameters:
- `file_path`: Path to the document
- `chunk_index`: Index of the chunk to retrieve
- `max_tokens`: Must match the value used in `get_section_chunks`

## Installation

**Requirements**: Python 3.10 or higher

1. Clone the docstrange repository:
```bash
git clone https://github.com/nanonets/docstrange.git
cd docstrange
```

2. Install in development mode:
```bash
pip install -e ".[dev]"
```

3. Install system dependencies for PDF processing:
```bash
# On macOS
brew install poppler

# On Ubuntu/Debian
sudo apt-get install poppler-utils

# On Windows
# Download poppler from: https://github.com/oschwartz10612/poppler-windows/releases/
```

## Configuration for Claude Code

### Using claude_desktop_config.json

Add the following to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "docstrange": {
      "command": "python3",
      "args": ["/path/to/docstrange/mcp_server_module/server.py"]
    }
  }
}
```

## Intelligent Processing Workflow

### Step 1: Parse and Analyze
```python
# Client pseudocode
response = mcp.call_tool("parse_pdf", {"file_path": "/path/to/document.pdf"})
info = mcp.call_tool("get_document_info", {"file_path": "/path/to/document.pdf"})
```

### Step 2: Choose Processing Strategy

Based on the `processing_recommendation` from `get_document_info`:

#### For Small Documents (< 8,000 tokens)
```python
# Process entire document at once
content = mcp.call_tool("get_full_content", {"file_path": "/path/to/document.pdf"})
# Work with the full content directly
```

#### For Medium Documents (8,000 - 32,000 tokens)
```python
# Option 1: Process full document if context allows
content = mcp.call_tool("get_full_content", {"file_path": "/path/to/document.pdf"})

# Option 2: Use chunking for efficiency
chunks = mcp.call_tool("get_section_chunks", {
    "file_path": "/path/to/document.pdf",
    "max_tokens": 4000
})
# Process chunks sequentially or in parallel
```

#### For Large Documents (32,000 - 128,000 tokens)
```python
# Use chunked processing
chunks = mcp.call_tool("get_section_chunks", {
    "file_path": "/path/to/document.pdf",
    "max_tokens": 4000
})

# Process each chunk
for i in range(len(chunks)):
    chunk_content = mcp.call_tool("get_chunk_content", {
        "file_path": "/path/to/document.pdf",
        "chunk_index": i,
        "max_tokens": 4000
    })
    # Process chunk_content
```

#### For Very Large Documents (> 128,000 tokens)
```python
# Use hierarchical navigation
structure = mcp.call_tool("get_hierarchical_structure", {
    "file_path": "/path/to/document.pdf"
})

# Navigate to specific sections of interest
headers = mcp.call_tool("get_headers", {
    "file_path": "/path/to/document.pdf",
    "max_level": 2  # Get only top-level sections
})

# Use search to find relevant sections
results = mcp.call_tool("search_document", {
    "file_path": "/path/to/document.pdf",
    "query": "specific topic"
})

# Load only relevant sections
section_content = mcp.call_tool("get_section", {
    "file_path": "/path/to/document.pdf",
    "section_title": "Relevant Section"
})
```

## Usage Examples

Once configured, you can use the MCP server in Claude Code:

### Basic Usage
```
# Parse a PDF file
Use the parse_pdf tool to load /path/to/document.pdf

# Get all headers in the document
Use the get_headers tool to list all sections in /path/to/document.pdf

# Search for specific content
Use the search_document tool to find "machine learning" in /path/to/document.pdf

# Get a specific section
Use the get_section tool to get the "Introduction" section from /path/to/document.pdf

# Get summaries of all sections
Use the get_section_summaries tool for /path/to/document.pdf with max_length 150
```

### Intelligent Usage
```
# Get document intelligence
Use the get_document_info tool to analyze /path/to/document.pdf

# Get hierarchical structure
Use the get_hierarchical_structure tool for /path/to/document.pdf

# Get smart chunks
Use the get_section_chunks tool for /path/to/document.pdf with max_tokens 4000

# Get specific chunk content
Use the get_chunk_content tool for chunk 0 from /path/to/document.pdf
```

## Testing the Server

You can test the MCP server standalone:

```bash
# Run the server from the docstrange root directory
python -m mcp_server_module

# Or directly
python mcp_server_module/server.py

# In another terminal, you can send test commands
# The server uses stdio for communication
```

## Token Counting Details

The server uses the `cl100k_base` tokenizer (compatible with GPT-4 and similar to Claude's tokenization) for accurate token counting. If the tokenizer is not available, it falls back to character-based estimation (approximately 4 characters per token).

### Token Limits Reference
- **Small Context (Claude Instant)**: ~8,000 tokens
- **Medium Context (GPT-4)**: ~32,000 tokens
- **Large Context (Claude 2)**: ~100,000 tokens
- **Extra Large Context (Claude 3)**: ~200,000 tokens

## Best Practices

1. **Always check document info first**: Use `get_document_info` to understand the document size and structure before processing.

2. **Use appropriate chunk sizes**: 
   - 2,000-4,000 tokens for detailed analysis
   - 8,000-16,000 tokens for summarization
   - Match your chunk size to your model's effective context window

3. **Implement fallback strategies**: If full document processing fails due to size, automatically fall back to chunked or hierarchical processing.

4. **Cache results**: The server caches parsed documents, so repeated operations on the same file are fast.

5. **Use search for large documents**: For documents over 100k tokens, always use search to find relevant sections rather than processing everything.

## Advanced Configuration

### Using GPU Processing

To enable GPU processing for better OCR performance, modify the server initialization in `mcp_server_module/server.py`:

```python
self.extractor = DocumentExtractor(
    preserve_layout=True,
    include_images=True,
    ocr_enabled=True,
    gpu=True  # Enable GPU processing
)
```

### Using Cloud Processing

For cloud-based processing with Nanonets API:

```python
self.extractor = DocumentExtractor(
    preserve_layout=True,
    include_images=True,
    ocr_enabled=True,
    api_key="your-nanonets-api-key"  # Get free API key from https://app.nanonets.com/#/keys
)
```

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError: No module named 'mcp'**
   - Solution: Install mcp package: `pip install mcp`

2. **PDF processing fails**
   - Ensure poppler is installed: `brew install poppler` (macOS) or `apt-get install poppler-utils` (Linux)

3. **Server not connecting to Claude Code**
   - Check the path in claude_desktop_config.json is absolute
   - Ensure Python environment has all dependencies installed
   - Restart Claude Desktop after configuration changes

4. **OCR not working properly**
   - The server uses EasyOCR by default for local processing
   - For better results, consider using GPU mode or cloud processing

### Debug Mode

To enable debug logging, modify the server:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Performance Considerations

- **Parsing**: First parse of a document may take time for OCR and model processing
- **Caching**: Subsequent operations on the same document are instant
- **Token Counting**: Adds minimal overhead (~1ms per section)
- **Chunking**: Smart chunking algorithm runs in O(n) time

## Error Handling

The server provides clear error messages for:
- Invalid file paths
- Corrupted PDFs
- Out-of-range chunk indices
- Missing sections

Always check the response status and handle errors appropriately in your client code.

## Development

To modify or extend the server:

1. The main server code is in `mcp_server_module/server.py`
2. Tools are defined in the `_setup_handlers` method
3. Document processing logic uses the docstrange library
4. Caching is implemented to avoid reprocessing documents

## License

MIT License - See LICENSE file for details