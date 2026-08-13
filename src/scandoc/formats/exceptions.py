"""
Exception classes for the multi-format ingestion framework.
"""


class FormatError(Exception):
    """Base exception for all format ingestion errors."""
    pass


class UnsupportedFormatError(FormatError):
    """Raised when no registered format provider can process the input document."""
    pass


class AmbiguousFormatError(FormatError):
    """Raised when format detection cannot unambiguously identify document type."""
    pass


class InvalidFileError(FormatError):
    """Raised when the input file or byte stream is corrupted, empty, or unreadable."""
    pass


class ProviderUnavailableError(FormatError):
    """Raised when a requested format provider is not installed or enabled."""
    pass


class ProviderExtractionError(FormatError):
    """Raised when a format provider fails during document parsing."""
    pass
