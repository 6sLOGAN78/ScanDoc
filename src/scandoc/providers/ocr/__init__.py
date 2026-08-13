"""
Multi-OCR Provider Subsystem for scanDOC.
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
from scandoc.providers.ocr.huggingface_adapter import (
    HuggingFaceOcrAdapter,
    HuggingFaceOcrConfig,
)
from scandoc.providers.ocr.models import (
    OcrCapability,
    OcrConfig,
    OcrProviderConfig,
    OCRResult,
    OCRTextRegion,
)
from scandoc.providers.ocr.rapidocr_provider import RapidOCRProvider
from scandoc.providers.ocr.registry import OcrProviderRegistry, default_ocr_registry
from scandoc.providers.ocr.remote_provider import (
    BaseHttpResponseAdapter,
    DefaultHttpResponseAdapter,
    GenericRemoteOcrProvider,
)
from scandoc.providers.ocr.secrets import SecretRef
from scandoc.providers.ocr.tesseract_provider import TesseractProvider

__all__ = [
    "BaseOcrProvider",
    "RapidOCRProvider",
    "TesseractProvider",
    "GenericRemoteOcrProvider",
    "BaseHttpResponseAdapter",
    "DefaultHttpResponseAdapter",
    "HuggingFaceOcrAdapter",
    "HuggingFaceOcrConfig",
    "OcrProviderRegistry",
    "default_ocr_registry",
    "OcrCapability",
    "OcrProviderConfig",
    "OCRResult",
    "OCRTextRegion",
    "SecretRef",
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
