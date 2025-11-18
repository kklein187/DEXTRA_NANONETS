"""Base processor class for document conversion."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..result import ConversionResult
from docstrange.config import InternalConfig
import os
import stat


class BaseProcessor(ABC):
    """Base class for all document processors."""
    
    def __init__(self, preserve_layout: bool = True, include_images: bool = False, ocr_enabled: bool = True, use_markdownify: bool = InternalConfig.use_markdownify):
        """Initialize the processor.
        
        Args:
            preserve_layout: Whether to preserve document layout
            include_images: Whether to include images in output
            ocr_enabled: Whether to enable OCR for image processing
            use_markdownify: Whether to use markdownify for HTML->Markdown conversion
        """
        self.preserve_layout = preserve_layout
        self.include_images = include_images
        self.ocr_enabled = ocr_enabled
        self.use_markdownify = use_markdownify
    
    @abstractmethod
    def can_process(self, file_path: str) -> bool:
        """Check if this processor can handle the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if this processor can handle the file
        """
        pass
    
    @abstractmethod
    def process(self, file_path: str) -> ConversionResult:
        """Process the file and return a conversion result.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            ConversionResult containing the processed content
            
        Raises:
            ConversionError: If processing fails
        """
        pass
    
    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get metadata about the file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary containing file metadata
        """
        try:
            stat = os.stat(file_path)
            # Ensure file_path is a string for splitext
            file_path_str = str(file_path)
            return {
                "file_size": stat.st_size,
                "file_extension": os.path.splitext(file_path_str)[1].lower(),
                "file_name": os.path.basename(file_path_str),
                "processor": self.__class__.__name__,
                "preserve_layout": self.preserve_layout,
                "include_images": self.include_images,
                "ocr_enabled": self.ocr_enabled
            }
        except Exception as e:
            logger.warning(f"Failed to get metadata for {file_path}: {e}")
            return {
                "processor": self.__class__.__name__,
                "preserve_layout": self.preserve_layout,
                "include_images": self.include_images,
                "ocr_enabled": self.ocr_enabled
            } 