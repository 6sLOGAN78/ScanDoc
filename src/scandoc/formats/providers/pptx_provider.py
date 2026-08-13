"""
PPTX Format Provider placeholder stub for Phase 4 framework.
"""

from pathlib import Path
from typing import BinaryIO, Optional, Set, Union

from scandoc.models.document import DocumentIR
from scandoc.formats.base import BaseFormatProvider
from scandoc.formats.exceptions import ProviderExtractionError


class PPTXFormatProvider(BaseFormatProvider):
    """
    Format Provider for Microsoft PowerPoint (.pptx) presentations.
    
    Registered as a placeholder stub in Phase 4.
    """

    @property
    def format_name(self) -> str:
        return "pptx"

    @property
    def supported_extensions(self) -> Set[str]:
        return {".pptx"}

    @property
    def supported_mime_types(self) -> Set[str]:
        return {"application/vnd.openxmlformats-officedocument.presentationml.presentation"}

    @property
    def is_fully_implemented(self) -> bool:
        return False

    @property
    def description(self) -> str:
        return "Microsoft PowerPoint PPTX Format Provider (Placeholder Stub)"

    def parse(
        self,
        source: Union[str, Path, bytes, bytearray, BinaryIO],
        file_path: Optional[str] = None,
    ) -> DocumentIR:
        raise ProviderExtractionError(
            "Extraction for PPTX format is not yet implemented in Phase 4"
        )
