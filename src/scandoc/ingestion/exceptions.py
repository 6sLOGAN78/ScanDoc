"""
Exception classes for Multi-Format Ingestion and Normalization subsystem.
"""


class IngestionError(Exception):
    """Base exception for all document ingestion errors."""
    pass


class UnsupportedFormatError(IngestionError):
    """Raised when an input document format is unsupported."""
    pass


class InvalidFileError(IngestionError):
    """Raised when an input file is missing, empty, or unreadable."""
    pass


class CorruptedDocumentError(IngestionError):
    """Raised when document binary payload is corrupted or unparseable."""
    pass


class ParserError(IngestionError):
    """Raised when format-specific native parser fails."""
    pass


class DependencyUnavailableError(IngestionError):
    """Raised when optional format parsing library (e.g. python-docx) is not installed."""
    pass


class OversizedInputError(IngestionError):
    """Raised when input payload exceeds maximum allowed size thresholds."""
    pass
