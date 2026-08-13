"""
OCR Subsystem for scanDOC: Base provider contracts, OCRResult models, and RapidOCR provider.
"""

from scandoc.providers.ocr.base import BaseOcrProvider
from scandoc.providers.ocr.converter import ocr_result_to_document_ir
from scandoc.providers.ocr.exceptions import (
    InvalidImageError,
    OcrConfigError,
    OcrError,
    OcrInferenceError,
    OcrInitializationError,
    OcrModelUnavailableError,
    OcrProviderUnavailableError,
    UnsupportedImageFormatError,
)
from scandoc.providers.ocr.models import OcrConfig, OCRResult, OCRTextRegion
from scandoc.providers.ocr.rapidocr_provider import RapidOCRProvider

__all__ = [
    "BaseOcrProvider",
    "RapidOCRProvider",
    "OCRResult",
    "OCRTextRegion",
    "OcrConfig",
    "ocr_result_to_document_ir",
    "OcrError",
    "OcrProviderUnavailableError",
    "OcrModelUnavailableError",
    "InvalidImageError",
    "UnsupportedImageFormatError",
    "OcrInferenceError",
    "OcrConfigError",
    "OcrInitializationError",
]
