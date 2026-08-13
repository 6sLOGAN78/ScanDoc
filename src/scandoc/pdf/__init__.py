"""
PDF Subsystem for scanDOC: Inspection, Native Extraction, and Backend Interfaces.
"""

from scandoc.pdf.backend import BasePdfBackend, PyPdfium2Backend
from scandoc.pdf.converter import NativePdfExtractor
from scandoc.pdf.exceptions import (
    EmptyPdfError,
    EncryptedPdfError,
    MalformedPdfError,
    PdfInspectionError,
)
from scandoc.pdf.inspector import PdfInspector
from scandoc.pdf.models import (
    DocumentCategory,
    ImageDetails,
    PageContentType,
    PageInspectionResult,
    PdfInspectionResult,
    PipelineSignals,
)
from scandoc.pdf.raw_models import (
    RawPdfImage,
    RawPdfLink,
    RawPdfMetadata,
    RawPdfPageData,
    RawPdfTextBlock,
    RawPdfTextSpan,
)

__all__ = [
    "PdfInspector",
    "NativePdfExtractor",
    "BasePdfBackend",
    "PyPdfium2Backend",
    "PdfInspectionResult",
    "PageInspectionResult",
    "ImageDetails",
    "PageContentType",
    "DocumentCategory",
    "PipelineSignals",
    "RawPdfPageData",
    "RawPdfTextBlock",
    "RawPdfTextSpan",
    "RawPdfImage",
    "RawPdfLink",
    "RawPdfMetadata",
    "PdfInspectionError",
    "MalformedPdfError",
    "EncryptedPdfError",
    "EmptyPdfError",
]
