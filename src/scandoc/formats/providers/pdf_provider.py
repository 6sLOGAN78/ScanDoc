"""
PDF Format Provider implementation backed by NativePdfExtractor.
"""

from pathlib import Path
from typing import BinaryIO, Optional, Set, Union

from scandoc.models.document import DocumentIR
from scandoc.pdf.converter import NativePdfExtractor
from scandoc.formats.base import BaseFormatProvider
from scandoc.formats.exceptions import ProviderExtractionError
from scandoc.formats.models import FormatDetectionResult


class PDFFormatProvider(BaseFormatProvider):
    """
    Format Provider for Portable Document Format (PDF).
    
    Fully implemented via scanDOC native PDF extraction pipeline.
    """

    def __init__(self):
        self._extractor = NativePdfExtractor()

    @property
    def format_name(self) -> str:
        return "pdf"

    @property
    def supported_extensions(self) -> Set[str]:
        return {".pdf"}

    @property
    def supported_mime_types(self) -> Set[str]:
        return {"application/pdf"}

    @property
    def is_fully_implemented(self) -> bool:
        return True

    @property
    def description(self) -> str:
        return "Native PDF Format Provider (Fully Implemented)"

    def parse(
        self,
        source: Union[str, Path, bytes, bytearray, BinaryIO],
        file_path: Optional[str] = None,
    ) -> DocumentIR:
        try:
            return self._extractor.extract(source, file_path=file_path)
        except Exception as e:
            if isinstance(e, ProviderExtractionError):
                raise
            raise ProviderExtractionError(f"PDF extraction failed: {e}") from e
