"""
Multi-Format Ingestion Framework for scanDOC.
"""

from scandoc.formats.base import BaseFormatProvider
from scandoc.formats.detector import FormatDetector
from scandoc.formats.exceptions import (
    AmbiguousFormatError,
    FormatError,
    InvalidFileError,
    ProviderExtractionError,
    ProviderUnavailableError,
    UnsupportedFormatError,
)
from scandoc.formats.models import FormatDetectionResult, ProviderInfo
from scandoc.formats.registry import FormatRegistry, default_registry

__all__ = [
    "BaseFormatProvider",
    "FormatDetector",
    "FormatRegistry",
    "default_registry",
    "FormatDetectionResult",
    "ProviderInfo",
    "FormatError",
    "UnsupportedFormatError",
    "AmbiguousFormatError",
    "InvalidFileError",
    "ProviderUnavailableError",
    "ProviderExtractionError",
]
