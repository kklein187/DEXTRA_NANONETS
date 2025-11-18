"""Text file processor."""

import os
from typing import Dict, Any

from .base import BaseProcessor
from ..result import ConversionResult
from ..exceptions import ConversionError, FileNotFoundError


class TXTProcessor(BaseProcessor):
    """Processor for plain text files."""
    
    def can_process(self, file_path: str) -> bool:
        """Check if this processor can handle the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if this processor can handle the file
        """
        if not os.path.exists(file_path):
            return False
        
        # Check file extension - ensure file_path is a string
        file_path_str = str(file_path)
        _, ext = os.path.splitext(file_path_str.lower())
        return ext in ['.txt', '.text']
    
    def process(self, file_path: str) -> ConversionResult:
        """Process the text file and return a conversion result.
        
        Args:
            file_path: Path to the text file to process
            
        Returns:
            ConversionResult containing the processed content
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ConversionError: If processing fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise ConversionError(f"Could not decode file {file_path} with any supported encoding")
            
            # Clean up the content
            content = self._clean_content(content)
            
            metadata = self.get_metadata(file_path)
            metadata.update({
                "encoding": encoding,
                "line_count": len(content.split('\n')),
                "word_count": len(content.split())
            })
            
            return ConversionResult(content, metadata)
            
        except Exception as e:
            if isinstance(e, (FileNotFoundError, ConversionError)):
                raise
            raise ConversionError(f"Failed to process text file {file_path}: {str(e)}")
    
    def _clean_content(self, content: str) -> str:
        """Clean up the text content.
        
        Args:
            content: Raw text content
            
        Returns:
            Cleaned text content
        """
        # Remove excessive whitespace
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove trailing whitespace
            line = line.rstrip()
            cleaned_lines.append(line)
        
        # Remove empty lines at the beginning and end
        while cleaned_lines and not cleaned_lines[0].strip():
            cleaned_lines.pop(0)
        
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        
        return '\n'.join(cleaned_lines) 