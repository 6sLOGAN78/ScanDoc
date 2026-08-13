"""
TXT Format Provider placeholder stub for Phase 4 framework.
"""

from pathlib import Path
from typing import BinaryIO, Optional, Set, Union

from scandoc.models.document import DocumentIR
from scandoc.formats.base import BaseFormatProvider
from scandoc.formats.exceptions import ProviderExtractionError


class TXTFormatProvider(BaseFormatProvider):
    """
    Format Provider for plain text (.txt) files.
    
    Registered as a placeholder stub in Phase 4.
    """

    @property
    def format_name(self) -> str:
        return "txt"

    @property
    def supported_extensions(self) -> Set[str]:
        return {".txt"}

    @property
    def supported_mime_types(self) -> Set[str]:
        return {"text/plain"}

    @property
    def is_fully_implemented(self) -> bool:
        return False

    @property
    def description(self) -> str:
        return "Plain Text TXT Format Provider (Placeholder Stub)"

    def parse(
        self,
        source: Union[str, Path, bytes, bytearray, BinaryIO],
        file_path: Optional[str] = None,
    ) -> DocumentIR:
        raise ProviderExtractionError(
            "Extraction for TXT format is not yet implemented in Phase 4"
        )
