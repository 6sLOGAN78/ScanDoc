"""
Markdown Format Provider placeholder stub for Phase 4 framework.
"""

from pathlib import Path
from typing import BinaryIO, Optional, Set, Union

from scandoc.models.document import DocumentIR
from scandoc.formats.base import BaseFormatProvider
from scandoc.formats.exceptions import ProviderExtractionError


class MarkdownFormatProvider(BaseFormatProvider):
    """
    Format Provider for Markdown (.md) documents.
    
    Registered as a placeholder stub in Phase 4.
    """

    @property
    def format_name(self) -> str:
        return "markdown"

    @property
    def supported_extensions(self) -> Set[str]:
        return {".md", ".markdown"}

    @property
    def supported_mime_types(self) -> Set[str]:
        return {"text/markdown"}

    @property
    def is_fully_implemented(self) -> bool:
        return False

    @property
    def description(self) -> str:
        return "Markdown Format Provider (Placeholder Stub)"

    def parse(
        self,
        source: Union[str, Path, bytes, bytearray, BinaryIO],
        file_path: Optional[str] = None,
    ) -> DocumentIR:
        raise ProviderExtractionError(
            "Extraction for Markdown format is not yet implemented in Phase 4"
        )
