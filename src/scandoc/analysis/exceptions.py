"""
Exception classes for Layout Analysis, Reading Order & Semantic Structure subsystem.
"""


class AnalysisError(Exception):
    """Base exception for all layout analysis and structural organization errors."""
    pass


class InvalidRegionError(AnalysisError):
    """Raised when a layout region geometry or bounding box is invalid."""
    pass


class ReadingOrderError(AnalysisError):
    """Raised when reading order graph or partitioning encounters cyclic or invalid dependencies."""
    pass


class ClassificationError(AnalysisError):
    """Raised when semantic block classification fails."""
    pass
