"""
Document Data Extractor - Extract structured data from any document into LLM-ready formats.
"""

from .extractor import DocumentExtractor
from .result import ConversionResult
from .processors import GPUConversionResult, CloudConversionResult
from .exceptions import ConversionError, UnsupportedFormatError
from .config import InternalConfig

__version__ = "1.1.5"
__all__ = [
    "DocumentExtractor", 
    "ConversionResult", 
    "GPUConversionResult",
    "CloudConversionResult",
    "ConversionError", 
    "UnsupportedFormatError", 
    "InternalConfig"
] 