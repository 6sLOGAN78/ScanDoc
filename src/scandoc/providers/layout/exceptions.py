"""
Exception classes for document layout analysis subsystem.
"""


class LayoutError(Exception):
    """Base exception for all document layout analysis errors."""
    pass


class LayoutProviderUnavailableError(LayoutError):
    """Raised when a requested layout provider or engine is not installed or model weights are missing."""
    pass


class LayoutModelError(LayoutError):
    """Raised when model loading or ONNX session initialization fails."""
    pass


class LayoutInitializationError(LayoutError):
    """Raised when layout provider initialization fails."""
    pass


class LayoutInferenceError(LayoutError):
    """Raised when layout model execution fails during image processing."""
    pass


class InvalidLayoutConfigError(LayoutError):
    """Raised when invalid layout configuration settings are provided."""
    pass
