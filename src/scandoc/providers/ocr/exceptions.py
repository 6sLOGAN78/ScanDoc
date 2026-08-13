"""
Custom exception classes for scanDOC OCR subsystem.
"""


class OcrError(Exception):
    """Base exception for all OCR subsystem errors."""
    pass


class OcrProviderUnavailableError(OcrError):
    """Raised when an OCR provider or engine is not installed or loaded."""
    pass


class OcrModelUnavailableError(OcrError):
    """Raised when required OCR model weights or checkpoints cannot be found."""
    pass


class InvalidImageError(OcrError):
    """Raised when the input image is corrupted, empty, or unreadable."""
    pass


class UnsupportedImageFormatError(OcrError):
    """Raised when the image format/extension is not supported by the OCR provider."""
    pass


class OcrInferenceError(OcrError):
    """Raised when OCR model execution fails during image processing."""
    pass


class OcrConfigError(OcrError):
    """Raised when invalid OCR configuration parameters are passed."""
    pass


class OcrInitializationError(OcrError):
    """Raised when an OCR provider fails during initialization."""
    pass
