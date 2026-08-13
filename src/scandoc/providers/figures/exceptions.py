"""
Exception classes for figure, image, and caption understanding subsystem.
"""


class FigureError(Exception):
    """Base exception for all figure and image understanding errors."""
    pass


class FigureProviderUnavailableError(FigureError):
    """Raised when a requested figure provider is not installed or model weights are missing."""
    pass


class PrivacyViolationError(FigureError):
    """Raised when a remote figure provider is invoked without explicit user permission."""
    pass


class FigureInferenceError(FigureError):
    """Raised when figure analysis model execution fails."""
    pass


class InvalidImageInputError(FigureError):
    """Raised when ImageInput payload is invalid or unreadable."""
    pass
