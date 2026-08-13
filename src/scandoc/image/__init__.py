"""
Image Processing & Preprocessing Subsystem for scanDOC.
"""

from scandoc.image.analysis import ImageAnalysis, ImageAnalyzer
from scandoc.image.exceptions import (
    ImageAnalysisError,
    ImageProcessingError,
    InvalidImageInputError,
    PreprocessingError,
)
from scandoc.image.operations import (
    AdaptiveThresholdOp,
    BaseImageOp,
    ContrastBrightnessOp,
    CropBorderOp,
    DenoiseOp,
    DeskewOp,
    GrayscaleOp,
    ResizeDpiOp,
    RotateOp,
    SharpenOp,
)
from scandoc.image.pipeline import (
    AdaptivePipelineBuilder,
    PreprocessedImage,
    PreprocessingPipeline,
)

__all__ = [
    "ImageAnalysis",
    "ImageAnalyzer",
    "PreprocessedImage",
    "PreprocessingPipeline",
    "AdaptivePipelineBuilder",
    "BaseImageOp",
    "GrayscaleOp",
    "ResizeDpiOp",
    "ContrastBrightnessOp",
    "DenoiseOp",
    "SharpenOp",
    "AdaptiveThresholdOp",
    "RotateOp",
    "DeskewOp",
    "CropBorderOp",
    "ImageProcessingError",
    "ImageAnalysisError",
    "PreprocessingError",
    "InvalidImageInputError",
]
