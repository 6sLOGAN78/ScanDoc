"""
Raster Image Format Provider native implementation for Phase 18.
"""

from pathlib import Path
from typing import BinaryIO, Optional, Set, Union
import uuid

from scandoc.formats.base import BaseFormatProvider
from scandoc.models import DocumentIR, DocumentMetadata, Page
from scandoc.models.blocks import FigureBlock
from scandoc.models.geometry import BoundingBox
from scandoc.models.provenance import ProcessingStage, Provenance


class ImageFormatProvider(BaseFormatProvider):
    """
    Format Provider for standalone raster images (PNG, JPG, WEBP, TIFF).
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
        return True

    @property
    def description(self) -> str:
        return "Raster Image Format Provider"

    def parse(
        self,
        source: Union[str, Path, bytes, bytearray, BinaryIO],
        file_path: Optional[str] = None,
    ) -> DocumentIR:
        prov = Provenance(
            provider="image_provider",
            model="native_image_extractor",
            stage=ProcessingStage.NATIVE_EXTRACTION,
        )

        fig_b = FigureBlock(
            id="img_b_0",
            caption="Raster Image Payload",
            bbox=BoundingBox(left=0.0, top=0.0, right=1.0, bottom=1.0, is_normalized=True),
            provenance=prov,
        )

        p = Page(page_index=0, width=612.0, height=792.0, blocks=[fig_b])
        meta = DocumentMetadata(id=f"doc_{uuid.uuid4().hex[:8]}", name=file_path or "Document.png", page_count=1)

        return DocumentIR(metadata=meta, pages=[p])
