"""
HTML Format Provider native implementation for Phase 18.
"""

from pathlib import Path
import re
from typing import BinaryIO, Optional, Set, Union
import uuid

from scandoc.formats.base import BaseFormatProvider
from scandoc.models import DocumentIR, DocumentMetadata, Page
from scandoc.models.blocks import HeadingBlock, ParagraphBlock
from scandoc.models.geometry import BoundingBox
from scandoc.models.provenance import ProcessingStage, Provenance


class HTMLFormatProvider(BaseFormatProvider):
    """
    Format Provider for HTML (.html, .htm) documents.
    Does NOT execute JavaScript or fetch remote URLs.
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
        return True

    @property
    def description(self) -> str:
        return "HTML Format Provider"

    def parse(
        self,
        source: Union[str, Path, bytes, bytearray, BinaryIO],
        file_path: Optional[str] = None,
    ) -> DocumentIR:
        if isinstance(source, (str, Path)):
            path_obj = Path(source)
            if path_obj.exists():
                raw_html = path_obj.read_text(encoding="utf-8", errors="replace")
            else:
                raw_html = str(source)
        elif isinstance(source, (bytes, bytearray)):
            raw_html = source.decode("utf-8", errors="replace")
        elif hasattr(source, "read"):
            buf = source.read()
            raw_html = buf.decode("utf-8", errors="replace") if isinstance(buf, bytes) else str(buf)
        else:
            raw_html = str(source)

        # Strip scripts and style tags safely
        clean_html = re.sub(r"<script.*?>.*?</script>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)
        clean_html = re.sub(r"<style.*?>.*?</style>", "", clean_html, flags=re.DOTALL | re.IGNORECASE)

        # Simple regex extraction for headings and paragraphs
        tags = re.findall(r"<(h[1-6]|p)>(.*?)</\1>", clean_html, flags=re.DOTALL | re.IGNORECASE)

        blocks = []
        prov = Provenance(
            provider="html_provider",
            model="native_html_extractor",
            stage=ProcessingStage.NATIVE_EXTRACTION,
        )

        if not tags:
            # Fallback to stripping all tags
            text_only = re.sub(r"<.*?>", "", clean_html).strip()
            if text_only:
                b = ParagraphBlock(
                    id="html_b_0",
                    text=text_only,
                    bbox=BoundingBox(left=0.0, top=0.0, right=1.0, bottom=1.0, is_normalized=True),
                    provenance=prov,
                )
                blocks.append(b)
        else:
            for idx, (tag_name, tag_text) in enumerate(tags):
                cleaned_text = re.sub(r"<.*?>", "", tag_text).strip()
                if not cleaned_text:
                    continue
                if tag_name.lower().startswith("h"):
                    level = int(tag_name[1])
                    b = HeadingBlock(
                        id=f"html_b_{idx}",
                        text=cleaned_text,
                        level=level,
                        bbox=BoundingBox(left=0.0, top=0.0, right=1.0, bottom=1.0, is_normalized=True),
                        provenance=prov,
                    )
                else:
                    b = ParagraphBlock(
                        id=f"html_b_{idx}",
                        text=cleaned_text,
                        bbox=BoundingBox(left=0.0, top=0.0, right=1.0, bottom=1.0, is_normalized=True),
                        provenance=prov,
                    )
                blocks.append(b)

        p = Page(page_index=0, width=612.0, height=792.0, blocks=blocks)
        meta = DocumentMetadata(id=f"doc_{uuid.uuid4().hex[:8]}", name=file_path or "Document.html", page_count=1)

        return DocumentIR(metadata=meta, pages=[p])
