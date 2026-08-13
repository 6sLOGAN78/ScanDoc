"""
Exception classes for reading order and document structure reconstruction.
"""


class ReadingOrderError(Exception):
    """Base exception for all reading order engine errors."""
    pass


class InvalidGeometryError(ReadingOrderError):
    """Raised when block or page geometry coordinates are invalid."""
    pass


class HierarchyReconstructionError(ReadingOrderError):
    """Raised when document section hierarchy reconstruction fails."""
    pass
