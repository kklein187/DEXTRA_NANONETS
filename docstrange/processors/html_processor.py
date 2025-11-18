"""HTML file processor."""

import os
import logging
from typing import Dict, Any

from .base import BaseProcessor
from ..result import ConversionResult
from ..exceptions import ConversionError, FileNotFoundError

# Configure logging
logger = logging.getLogger(__name__)


class HTMLProcessor(BaseProcessor):
    """Processor for HTML files using markdownify for conversion."""
    
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
        return ext in ['.html', '.htm']
    
    def process(self, file_path: str) -> ConversionResult:
        """Process the HTML file and return a conversion result.
        
        Args:
            file_path: Path to the HTML file to process
            
        Returns:
            ConversionResult containing the processed content
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ConversionError: If processing fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            try:
                from markdownify import markdownify as md
            except ImportError:
                raise ConversionError("markdownify is required for HTML processing. Install it with: pip install markdownify")

            metadata = self.get_metadata(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            content = md(html_content, heading_style="ATX")
            return ConversionResult(content, metadata)
        except Exception as e:
            if isinstance(e, (FileNotFoundError, ConversionError)):
                raise
            raise ConversionError(f"Failed to process HTML file {file_path}: {str(e)}") 