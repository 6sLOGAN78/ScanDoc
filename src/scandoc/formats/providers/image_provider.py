"""
Raster Image Format Provider placeholder stub for Phase 4 framework.
"""

from pathlib import Path
from typing import BinaryIO, Optional, Set, Union

from scandoc.models.document import DocumentIR
from scandoc.formats.base import BaseFormatProvider
from scandoc.formats.exceptions import ProviderExtractionError


class ImageFormatProvider(BaseFormatProvider):
    """
    Format Provider for standalone raster images (PNG, JPG, WEBP, TIFF).
    
    Registered as a placeholder stub in Phase 4.
    """

    @property
    def format_name(self) -> str:
        return "image"

    @property
    def supported_extensions(self) -> Set[str]:
        return {".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tif"}

    @property
    def supported_mime_types(self) -> Set[str]:
        return {"image/png", "image/jpeg", "image/webp", "image/tiff"}

    @property
    def is_fully_implemented(self) -> bool:
        return False

    @property
    def description(self) -> str:
        return "Raster Image Format Provider (Placeholder Stub)"

    def parse(
        self,
        source: Union[str, Path, bytes, bytearray, BinaryIO],
        file_path: Optional[str] = None,
    ) -> DocumentIR:
        raise ProviderExtractionError(
            "Extraction for Image format is not yet implemented in Phase 4"
        )
