"""Custom exceptions for the LLM Data Converter library."""


class ConversionError(Exception):
    """Raised when document conversion fails."""
    pass


class UnsupportedFormatError(Exception):
    """Raised when the input format is not supported."""
    pass


class FileNotFoundError(Exception):
    """Raised when the input file is not found."""
    pass


class NetworkError(Exception):
    """Raised when network operations fail (e.g., URL fetching)."""
    pass 