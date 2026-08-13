"""
HTML Format Provider placeholder stub for Phase 4 framework.
"""

from pathlib import Path
from typing import BinaryIO, Optional, Set, Union

from scandoc.models.document import DocumentIR
from scandoc.formats.base import BaseFormatProvider
from scandoc.formats.exceptions import ProviderExtractionError


class HTMLFormatProvider(BaseFormatProvider):
    """
    Format Provider for HTML document pages.
    
    Registered as a placeholder stub in Phase 4.
    """

    @property
    def format_name(self) -> str:
        return "html"

    @property
    def supported_extensions(self) -> Set[str]:
        return {".html", ".htm"}

    @property
    def supported_mime_types(self) -> Set[str]:
        return {"text/html"}

    @property
    def is_fully_implemented(self) -> bool:
        return False

    @property
    def description(self) -> str:
        return "HTML Format Provider (Placeholder Stub)"

    def parse(
        self,
        source: Union[str, Path, bytes, bytearray, BinaryIO],
        file_path: Optional[str] = None,
    ) -> DocumentIR:
        raise ProviderExtractionError(
            "Extraction for HTML format is not yet implemented in Phase 4"
        )
