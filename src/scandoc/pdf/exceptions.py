"""
Custom exceptions for the scanDOC PDF inspection subsystem.
"""


class PdfInspectionError(Exception):
    """Base exception for all PDF inspection errors."""
    pass


class MalformedPdfError(PdfInspectionError):
    """Raised when the input PDF is corrupted, malformed, or unparseable."""
    pass


class EncryptedPdfError(PdfInspectionError):
    """Raised when the input PDF is password-protected or encrypted."""
    pass


class EmptyPdfError(PdfInspectionError):
    """Raised when the input PDF has 0 pages or no valid content."""
    pass
