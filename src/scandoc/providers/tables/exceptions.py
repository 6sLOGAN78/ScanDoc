"""
Exception classes for table structure recognition subsystem.
"""


class TableError(Exception):
    """Base exception for all table structure recognition errors."""
    pass


class TableProviderUnavailableError(TableError):
    """Raised when a requested table provider or model weights are missing."""
    pass


class TableInitializationError(TableError):
    """Raised when table provider model initialization fails."""
    pass


class TableInferenceError(TableError):
    """Raised when table structure inference fails."""
    pass
