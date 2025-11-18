#!/usr/bin/env python3
"""MCP Server for PDF document processing using docstrange."""

import os
import sys
import re
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import asyncio
import tiktoken

from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from mcp.server.stdio import stdio_server

from docstrange import DocumentExtractor
from docstrange.result import ConversionResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DocumentSection:
    """Represents a section in a document."""
    level: int
    title: str
    content: str
    start_line: int
    end_line: int
    token_count: int = 0
    
@dataclass
class DocumentCache:
    """Cache for processed documents."""
    file_path: str
    markdown_content: str
    sections: List[DocumentSection]
    metadata: Dict[str, Any]
    file_hash: str
    total_tokens: int = 0
    hierarchical_structure: Optional[Dict] = None

class DocstrangeServer:
    """MCP Server for document processing using docstrange."""
    
    def __init__(self):
        self.server = Server("docstrange")
        self.document_cache: Dict[str, DocumentCache] = {}
        self.extractor = None  # Initialize lazily to avoid model downloads at startup
        self.tokenizer = None  # Initialize lazily
        self._setup_handlers()
    
    def _get_extractor(self):
        """Lazily initialize the document extractor."""
        if self.extractor is None:
            logger.info("Initializing DocumentExtractor...")
            self.extractor = DocumentExtractor()
        return self.extractor
    
    def _get_tokenizer(self):
        """Lazily initialize the tokenizer for token counting."""
        if self.tokenizer is None:
            try:
                # Use cl100k_base encoding (GPT-4, Claude compatible approximation)
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
            except Exception as e:
                logger.warning(f"Failed to load tokenizer: {e}. Using character-based estimation.")
                self.tokenizer = None
        return self.tokenizer
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken or fallback to character estimation."""
        tokenizer = self._get_tokenizer()
        if tokenizer:
            return len(tokenizer.encode(text))
        else:
            # Rough estimation: ~4 characters per token on average
            return len(text) // 4
    
    def _get_file_hash(self, file_path: str) -> str:
        """Calculate hash of a file for cache invalidation."""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def _parse_markdown_sections(self, markdown_content: str) -> List[DocumentSection]:
        """Parse markdown content into sections based on headers."""
        sections = []
        lines = markdown_content.split('\n')
        
        current_section = None
        section_start = 0
        
        for i, line in enumerate(lines):
            # Check if line is a header
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                # Save previous section if exists
                if current_section:
                    current_section.end_line = i - 1
                    current_section.content = '\n'.join(lines[current_section.start_line:current_section.end_line + 1])
                    current_section.token_count = self._count_tokens(current_section.content)
                    sections.append(current_section)
                
                # Start new section
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                current_section = DocumentSection(
                    level=level,
                    title=title,
                    content="",
                    start_line=i,
                    end_line=i,
                    token_count=0
                )
                section_start = i + 1
        
        # Save last section
        if current_section:
            current_section.end_line = len(lines) - 1
            current_section.content = '\n'.join(lines[current_section.start_line:current_section.end_line + 1])
            current_section.token_count = self._count_tokens(current_section.content)
            sections.append(current_section)
        
        # If no sections found, treat entire content as one section
        if not sections and markdown_content:
            content = markdown_content
            sections.append(DocumentSection(
                level=0,
                title="Document Content",
                content=content,
                start_line=0,
                end_line=len(lines) - 1,
                token_count=self._count_tokens(content)
            ))
        
        return sections
    
    def _build_hierarchical_structure(self, sections: List[DocumentSection]) -> Dict:
        """Build a hierarchical structure from flat sections list."""
        def build_tree(sections, parent_level=0):
            tree = []
            i = 0
            while i < len(sections):
                section = sections[i]
                if section.level <= parent_level and parent_level > 0:
                    break
                    
                node = {
                    "title": section.title,
                    "level": section.level,
                    "token_count": section.token_count,
                    "start_line": section.start_line,
                    "end_line": section.end_line,
                    "children": []
                }
                
                # Find children
                if i + 1 < len(sections) and sections[i + 1].level > section.level:
                    # Get all subsequent sections with higher level
                    child_sections = []
                    j = i + 1
                    while j < len(sections) and sections[j].level > section.level:
                        child_sections.append(sections[j])
                        j += 1
                    node["children"] = build_tree(child_sections, section.level)
                    i = j
                else:
                    i += 1
                    
                tree.append(node)
            return tree
        
        return {"structure": build_tree(sections), "total_sections": len(sections)}
    
    def _get_section_chunks(self, doc_cache: DocumentCache, max_tokens: int = 4000) -> List[Dict[str, Any]]:
        """Get document chunks that fit within token limit."""
        chunks = []
        current_chunk = {
            "sections": [],
            "token_count": 0,
            "start_index": 0,
            "end_index": 0
        }
        
        for i, section in enumerate(doc_cache.sections):
            if current_chunk["token_count"] + section.token_count <= max_tokens:
                current_chunk["sections"].append({
                    "title": section.title,
                    "level": section.level,
                    "tokens": section.token_count
                })
                current_chunk["token_count"] += section.token_count
                current_chunk["end_index"] = i
            else:
                if current_chunk["sections"]:
                    chunks.append(current_chunk)
                current_chunk = {
                    "sections": [{
                        "title": section.title,
                        "level": section.level,
                        "tokens": section.token_count
                    }],
                    "token_count": section.token_count,
                    "start_index": i,
                    "end_index": i
                }
        
        if current_chunk["sections"]:
            chunks.append(current_chunk)
        
        return chunks
    
    def _load_document(self, file_path: str) -> DocumentCache:
        """Load and cache a document."""
        abs_path = os.path.abspath(file_path)
        
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"File not found: {abs_path}")
        
        # Check cache
        file_hash = self._get_file_hash(abs_path)
        if abs_path in self.document_cache:
            cached = self.document_cache[abs_path]
            if cached.file_hash == file_hash:
                return cached
        
        # Process document
        logger.info(f"Processing document: {abs_path}")
        extractor = self._get_extractor()
        result: ConversionResult = extractor.extract(abs_path)
        
        # Parse sections
        markdown_content = result.extract_markdown()
        sections = self._parse_markdown_sections(markdown_content)
        
        # Calculate total tokens
        total_tokens = self._count_tokens(markdown_content)
        
        # Build hierarchical structure
        hierarchical_structure = self._build_hierarchical_structure(sections)
        
        # Cache the result
        doc_cache = DocumentCache(
            file_path=abs_path,
            markdown_content=markdown_content,
            sections=sections,
            metadata=result.metadata,
            file_hash=file_hash,
            total_tokens=total_tokens,
            hierarchical_structure=hierarchical_structure
        )
        self.document_cache[abs_path] = doc_cache
        
        return doc_cache
    
    def _search_in_document(self, doc_cache: DocumentCache, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search for a query in the document."""
        results = []
        lines = doc_cache.markdown_content.split('\n')
        
        # Prepare search pattern
        if not case_sensitive:
            query = query.lower()
        
        for i, line in enumerate(lines):
            search_line = line if case_sensitive else line.lower()
            if query in search_line:
                # Find which section this line belongs to
                section_title = "Unknown Section"
                for section in doc_cache.sections:
                    if section.start_line <= i <= section.end_line:
                        section_title = section.title
                        break
                
                # Get context (2 lines before and after)
                context_start = max(0, i - 2)
                context_end = min(len(lines), i + 3)
                context = '\n'.join(lines[context_start:context_end])
                
                results.append({
                    "line_number": i + 1,
                    "line_content": line,
                    "section": section_title,
                    "context": context
                })
        
        return results
    
    def _get_section_summary(self, section: DocumentSection, max_length: int = 200) -> str:
        """Generate a summary of a section."""
        content = section.content.strip()
        if len(content) <= max_length:
            return content
        
        # Simple truncation with ellipsis
        return content[:max_length] + "..."
    
    def _get_processing_recommendation(self, total_tokens: int) -> Dict[str, Any]:
        """Get processing recommendation based on token count."""
        # Common context window sizes
        SMALL_CONTEXT = 8000
        MEDIUM_CONTEXT = 32000
        LARGE_CONTEXT = 128000
        
        if total_tokens < SMALL_CONTEXT:
            return {
                "approach": "full_document",
                "reason": f"Document fits in small context ({total_tokens} tokens < {SMALL_CONTEXT})",
                "strategy": "Process entire document at once"
            }
        elif total_tokens < MEDIUM_CONTEXT:
            return {
                "approach": "full_document_or_chunked",
                "reason": f"Document fits in medium context ({total_tokens} tokens < {MEDIUM_CONTEXT})",
                "strategy": "Can process full document or use chunks for efficiency"
            }
        elif total_tokens < LARGE_CONTEXT:
            return {
                "approach": "chunked_processing",
                "reason": f"Document fits in large context but benefits from chunking ({total_tokens} tokens)",
                "strategy": "Use hierarchical navigation and chunk processing"
            }
        else:
            return {
                "approach": "hierarchical_navigation",
                "reason": f"Document exceeds large context ({total_tokens} tokens > {LARGE_CONTEXT})",
                "strategy": "Must use hierarchical navigation, search, and selective section loading"
            }
    
    def _setup_handlers(self):
        """Setup MCP server handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="parse_pdf",
                    description="Parse a PDF file and load it into memory for navigation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the PDF file to parse"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="get_headers",
                    description="Get all headers/sections from a parsed document",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the previously parsed PDF file"
                            },
                            "max_level": {
                                "type": "integer",
                                "description": "Maximum header level to include (1-6)",
                                "default": 6
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="search_document",
                    description="Search for keywords or phrases in the document",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the previously parsed PDF file"
                            },
                            "query": {
                                "type": "string",
                                "description": "Search query (keyword or phrase)"
                            },
                            "case_sensitive": {
                                "type": "boolean",
                                "description": "Whether search should be case sensitive",
                                "default": False
                            }
                        },
                        "required": ["file_path", "query"]
                    }
                ),
                Tool(
                    name="get_section",
                    description="Get the content of a specific section by title",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the previously parsed PDF file"
                            },
                            "section_title": {
                                "type": "string",
                                "description": "Title of the section to retrieve"
                            }
                        },
                        "required": ["file_path", "section_title"]
                    }
                ),
                Tool(
                    name="get_section_summaries",
                    description="Get summaries of all sections in the document",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the previously parsed PDF file"
                            },
                            "max_length": {
                                "type": "integer",
                                "description": "Maximum length of each summary",
                                "default": 200
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="get_full_content",
                    description="Get the full markdown content of the document",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the previously parsed PDF file"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="list_cached_documents",
                    description="List all documents currently cached in memory",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_document_info",
                    description="Get document metadata including token count, section structure, and recommendations for processing",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the previously parsed PDF file"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="get_hierarchical_structure",
                    description="Get the hierarchical tree structure of document sections",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the previously parsed PDF file"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="get_section_chunks",
                    description="Get document divided into chunks that fit within a token limit",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the previously parsed PDF file"
                            },
                            "max_tokens": {
                                "type": "integer",
                                "description": "Maximum tokens per chunk",
                                "default": 4000
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="get_chunk_content",
                    description="Get the content of a specific chunk by index",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the previously parsed PDF file"
                            },
                            "chunk_index": {
                                "type": "integer",
                                "description": "Index of the chunk to retrieve"
                            },
                            "max_tokens": {
                                "type": "integer",
                                "description": "Maximum tokens per chunk (must match what was used in get_section_chunks)",
                                "default": 4000
                            }
                        },
                        "required": ["file_path", "chunk_index"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent | EmbeddedResource]:
            """Handle tool calls."""
            
            try:
                if name == "parse_pdf":
                    file_path = arguments["file_path"]
                    doc_cache = self._load_document(file_path)
                    
                    response = {
                        "status": "success",
                        "file_path": doc_cache.file_path,
                        "sections_count": len(doc_cache.sections),
                        "total_lines": len(doc_cache.markdown_content.split('\n')),
                        "metadata": doc_cache.metadata
                    }
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps(response, indent=2)
                    )]
                
                elif name == "get_headers":
                    file_path = arguments["file_path"]
                    max_level = arguments.get("max_level", 6)
                    
                    doc_cache = self._load_document(file_path)
                    headers = []
                    
                    for section in doc_cache.sections:
                        if section.level <= max_level:
                            headers.append({
                                "level": section.level,
                                "title": section.title,
                                "line_start": section.start_line,
                                "line_end": section.end_line
                            })
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps(headers, indent=2)
                    )]
                
                elif name == "search_document":
                    file_path = arguments["file_path"]
                    query = arguments["query"]
                    case_sensitive = arguments.get("case_sensitive", False)
                    
                    doc_cache = self._load_document(file_path)
                    results = self._search_in_document(doc_cache, query, case_sensitive)
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps(results, indent=2)
                    )]
                
                elif name == "get_section":
                    file_path = arguments["file_path"]
                    section_title = arguments["section_title"]
                    
                    doc_cache = self._load_document(file_path)
                    
                    for section in doc_cache.sections:
                        if section.title.lower() == section_title.lower():
                            return [TextContent(
                                type="text",
                                text=section.content
                            )]
                    
                    return [TextContent(
                        type="text",
                        text=f"Section '{section_title}' not found"
                    )]
                
                elif name == "get_section_summaries":
                    file_path = arguments["file_path"]
                    max_length = arguments.get("max_length", 200)
                    
                    doc_cache = self._load_document(file_path)
                    summaries = []
                    
                    for section in doc_cache.sections:
                        summaries.append({
                            "title": section.title,
                            "level": section.level,
                            "summary": self._get_section_summary(section, max_length)
                        })
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps(summaries, indent=2)
                    )]
                
                elif name == "get_full_content":
                    file_path = arguments["file_path"]
                    doc_cache = self._load_document(file_path)
                    
                    return [TextContent(
                        type="text",
                        text=doc_cache.markdown_content
                    )]
                
                elif name == "list_cached_documents":
                    cached_docs = []
                    for path, cache in self.document_cache.items():
                        cached_docs.append({
                            "file_path": path,
                            "sections_count": len(cache.sections),
                            "file_hash": cache.file_hash,
                            "total_tokens": cache.total_tokens
                        })
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps(cached_docs, indent=2)
                    )]
                
                elif name == "get_document_info":
                    file_path = arguments["file_path"]
                    doc_cache = self._load_document(file_path)
                    
                    # Analyze document and provide recommendations
                    info = {
                        "file_path": doc_cache.file_path,
                        "total_tokens": doc_cache.total_tokens,
                        "total_sections": len(doc_cache.sections),
                        "total_lines": len(doc_cache.markdown_content.split('\n')),
                        "metadata": doc_cache.metadata,
                        "token_distribution": {
                            "min": min(s.token_count for s in doc_cache.sections) if doc_cache.sections else 0,
                            "max": max(s.token_count for s in doc_cache.sections) if doc_cache.sections else 0,
                            "avg": sum(s.token_count for s in doc_cache.sections) // len(doc_cache.sections) if doc_cache.sections else 0
                        },
                        "processing_recommendation": self._get_processing_recommendation(doc_cache.total_tokens),
                        "suggested_chunk_count": len(self._get_section_chunks(doc_cache, 4000))
                    }
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps(info, indent=2)
                    )]
                
                elif name == "get_hierarchical_structure":
                    file_path = arguments["file_path"]
                    doc_cache = self._load_document(file_path)
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps(doc_cache.hierarchical_structure, indent=2)
                    )]
                
                elif name == "get_section_chunks":
                    file_path = arguments["file_path"]
                    max_tokens = arguments.get("max_tokens", 4000)
                    
                    doc_cache = self._load_document(file_path)
                    chunks = self._get_section_chunks(doc_cache, max_tokens)
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps(chunks, indent=2)
                    )]
                
                elif name == "get_chunk_content":
                    file_path = arguments["file_path"]
                    chunk_index = arguments["chunk_index"]
                    max_tokens = arguments.get("max_tokens", 4000)
                    
                    doc_cache = self._load_document(file_path)
                    chunks = self._get_section_chunks(doc_cache, max_tokens)
                    
                    if chunk_index < 0 or chunk_index >= len(chunks):
                        return [TextContent(
                            type="text",
                            text=f"Invalid chunk index. Document has {len(chunks)} chunks."
                        )]
                    
                    chunk = chunks[chunk_index]
                    # Get actual content for this chunk
                    content_parts = []
                    for i in range(chunk["start_index"], chunk["end_index"] + 1):
                        if i < len(doc_cache.sections):
                            content_parts.append(doc_cache.sections[i].content)
                    
                    return [TextContent(
                        type="text",
                        text='\n\n'.join(content_parts)
                    )]
                
                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )]
                    
            except Exception as e:
                logger.error(f"Error executing tool {name}: {str(e)}")
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "error": str(e)
                    }, indent=2)
                )]
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                initialization_options=self.server.create_initialization_options()
            )

async def main():
    """Main entry point."""
    server = DocstrangeServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())