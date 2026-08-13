"""
TXT Format Provider native implementation for Phase 18.
"""

from pathlib import Path
from typing import BinaryIO, Optional, Set, Union
import uuid

from scandoc.formats.base import BaseFormatProvider
from scandoc.models import DocumentIR, DocumentMetadata, Page
from scandoc.models.blocks import ParagraphBlock
from scandoc.models.geometry import BoundingBox
from scandoc.models.provenance import ProcessingStage, Provenance


class TXTFormatProvider(BaseFormatProvider):
    """
    Format Provider for plain text (.txt) files.
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
        return True

    @property
    def description(self) -> str:
        return "Plain Text TXT Format Provider"

    def parse(
        self,
        source: Union[str, Path, bytes, bytearray, BinaryIO],
        file_path: Optional[str] = None,
    ) -> DocumentIR:
        # Read text content
        if isinstance(source, (str, Path)):
            path_obj = Path(source)
            if path_obj.exists():
                text_content = path_obj.read_text(encoding="utf-8", errors="replace")
            else:
                text_content = str(source)
        elif isinstance(source, (bytes, bytearray)):
            text_content = source.decode("utf-8", errors="replace")
        elif hasattr(source, "read"):
            buf = source.read()
            text_content = buf.decode("utf-8", errors="replace") if isinstance(buf, bytes) else str(buf)
        else:
            text_content = str(source)

        lines = [line.strip() for line in text_content.splitlines() if line.strip()]

        blocks = []
        prov = Provenance(
            provider="txt_provider",
            model="native_txt_extractor",
            stage=ProcessingStage.NATIVE_EXTRACTION,
        )

        for idx, line in enumerate(lines):
            b = ParagraphBlock(
                id=f"txt_b_{idx}",
                text=line,
                bbox=BoundingBox(left=0.0, top=0.0, right=1.0, bottom=1.0, is_normalized=True),
                provenance=prov,
            )
            blocks.append(b)

        p = Page(page_index=0, width=612.0, height=792.0, blocks=blocks)
        meta = DocumentMetadata(id=f"doc_{uuid.uuid4().hex[:8]}", name=file_path or "Document.txt", page_count=1)

        return DocumentIR(metadata=meta, pages=[p])
