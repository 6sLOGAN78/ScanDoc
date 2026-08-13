"""
Exception classes for image analysis and preprocessing pipeline.
"""


class ImageProcessingError(Exception):
    """Base exception for all image processing and preprocessing errors."""
    pass


class ImageAnalysisError(ImageProcessingError):
    """Raised when image quality analysis fails."""
    pass


class PreprocessingError(ImageProcessingError):
    """Raised when a specific image preprocessing operation fails."""
    pass


class InvalidImageInputError(ImageProcessingError):
    """Raised when input image source is missing, empty, or unreadable."""
    pass
