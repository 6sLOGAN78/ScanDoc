"""
Exception classes for Model Management and Local Model Runtime subsystem.
"""


class ModelManagementError(Exception):
    """Base exception for all model management errors."""
    pass


class ModelNotFoundError(ModelManagementError):
    """Raised when a requested model is not found in registry or local store."""
    pass


class ModelDownloadError(ModelManagementError):
    """Raised when model downloading fails or is interrupted."""
    pass


class ModelValidationError(ModelManagementError):
    """Raised when model verification, checksum, or format validation fails."""
    pass


class OfflineModeError(ModelManagementError):
    """Raised when network acquisition is attempted while offline mode is active."""
    pass


class InsufficientDiskSpaceError(ModelManagementError):
    """Raised when available disk space is insufficient for model acquisition."""
    pass


class ModelLoadError(ModelManagementError):
    """Raised when model loading into memory fails."""
    pass
