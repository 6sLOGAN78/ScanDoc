"""
Abstract backend contract and PyPdfium2 implementation for native PDF extraction.
"""

from abc import ABC, abstractmethod
import io
import logging
from pathlib import Path
from typing import BinaryIO, Dict, List, Optional, Union

import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_c

from scandoc.pdf.exceptions import (
    EmptyPdfError,
    EncryptedPdfError,
    MalformedPdfError,
    PdfInspectionError,
)
from scandoc.pdf.raw_models import (
    RawPdfImage,
    RawPdfLink,
    RawPdfMetadata,
    RawPdfPageData,
    RawPdfTextBlock,
    RawPdfTextSpan,
)

logger = logging.getLogger("scandoc.pdf.backend")


class BasePdfBackend(ABC):
    """
    Abstract base class for PDF parsing backends.
    
    Decouples PDF parsing libraries from scanDOC DocumentIR assembly.
    """

    @abstractmethod
    def open(self, source: Union[str, Path, bytes, bytearray, BinaryIO]) -> None:
        """Open PDF document source."""
        pass

    @abstractmethod
    def extract_metadata(self) -> RawPdfMetadata:
        """Extract document-level catalog metadata."""
        pass

    @abstractmethod
    def extract_page(self, page_index: int) -> RawPdfPageData:
        """Extract raw text blocks, images, links, and dimensions for page."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Release underlying PDF document resources."""
        pass

    def __enter__(self) -> "BasePdfBackend":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


class PyPdfium2Backend(BasePdfBackend):
    """
    High-performance native PDF backend implemented using PyPDFium2 C++ bindings.
    """

    def __init__(self, source: Optional[Union[str, Path, bytes, bytearray, BinaryIO]] = None):
        self._pdf: Optional[pdfium.PdfDocument] = None
        self._source_size: int = 0
        if source is not None:
            self.open(source)

    def open(self, source: Union[str, Path, bytes, bytearray, BinaryIO]) -> None:
        if isinstance(source, (str, Path)):
            path_obj = Path(source)
            if not path_obj.exists():
                raise PdfInspectionError(f"PDF file not found: {source}")
            self._source_size = path_obj.stat().st_size
            pdf_input = str(path_obj.resolve())
        elif isinstance(source, (bytes, bytearray)):
            self._source_size = len(source)
            pdf_input = bytes(source)
        elif hasattr(source, "read"):
            content = source.read()
            self._source_size = len(content)
            pdf_input = content
        else:
            raise PdfInspectionError(f"Unsupported source type: {type(source)}")

        if self._source_size == 0:
            raise EmptyPdfError("PDF source is 0 bytes")

        try:
            self._pdf = pdfium.PdfDocument(pdf_input)
        except pdfium.PdfiumError as e:
            err_msg = str(e).lower()
            if "password" in err_msg or "encrypted" in err_msg:
                raise EncryptedPdfError("PDF is password protected") from e
            raise MalformedPdfError(f"Malformed or corrupted PDF: {e}") from e
        except Exception as e:
            raise MalformedPdfError(f"Failed to open PDF document: {e}") from e

        if len(self._pdf) == 0:
            raise EmptyPdfError("PDF contains 0 pages")

    def extract_metadata(self) -> RawPdfMetadata:
        if self._pdf is None:
            raise PdfInspectionError("Backend document is not open")

        raw_meta = self._pdf.get_metadata_dict()
        extra_meta = {
            k: v for k, v in raw_meta.items()
            if k not in ("Title", "Author", "Subject", "Creator", "Producer", "CreationDate", "ModDate")
        }

        return RawPdfMetadata(
            title=raw_meta.get("Title") or None,
            author=raw_meta.get("Author") or None,
            subject=raw_meta.get("Subject") or None,
            creator=raw_meta.get("Creator") or None,
            producer=raw_meta.get("Producer") or None,
            creation_date=raw_meta.get("CreationDate") or None,
            mod_date=raw_meta.get("ModDate") or None,
            page_count=len(self._pdf),
            extra=extra_meta,
        )

    def extract_page(self, page_index: int) -> RawPdfPageData:
        if self._pdf is None:
            raise PdfInspectionError("Backend document is not open")

        if page_index < 0 or page_index >= len(self._pdf):
            raise PdfInspectionError(f"Page index {page_index} out of bounds (0..{len(self._pdf)-1})")

        page = self._pdf[page_index]
        width = float(page.get_width())
        height = float(page.get_height())
        rotation = int(page.get_rotation()) % 360

        text_blocks = self._extract_text_blocks(page, width, height)
        images = self._extract_images(page, width, height)
        links = self._extract_links(page)

        return RawPdfPageData(
            page_index=page_index,
            width=width,
            height=height,
            rotation=rotation,
            text_blocks=text_blocks,
            images=images,
            links=links,
        )

    def _extract_text_blocks(
        self, page: pdfium.PdfPage, width: float, height: float
    ) -> List[RawPdfTextBlock]:
        """Extract character streams and group them into line-level text blocks with PDF bboxes."""
        text_page = page.get_textpage()
        char_count = text_page.count_chars()
        if char_count <= 0:
            return []

        # Segment raw text range into lines
        full_text = text_page.get_text_bounded()
        lines = full_text.splitlines()

        blocks: List[RawPdfTextBlock] = []
        char_ptr = 0
        seq_idx = 0

        for line_str in lines:
            line_clean = line_str.strip()
            if not line_clean:
                char_ptr += len(line_str) + 1  # Include newline
                continue

            # Find matching char range for this line
            start_idx = full_text.find(line_str, char_ptr)
            if start_idx == -1:
                start_idx = char_ptr
            end_idx = start_idx + len(line_str)
            char_ptr = end_idx

            # Collect character bounding boxes for line
            min_l, min_b = float("inf"), float("inf")
            max_r, max_t = float("-inf"), float("-inf")
            has_valid_chars = False

            for c_idx in range(start_idx, min(end_idx, char_count)):
                try:
                    c_box = text_page.get_charbox(c_idx)
                    # c_box is (left, bottom, right, top)
                    cl, cb, cr, ct = float(c_box[0]), float(c_box[1]), float(c_box[2]), float(c_box[3])
                    if cr > cl and ct > cb:
                        min_l = min(min_l, cl)
                        min_b = min(min_b, cb)
                        max_r = max(max_r, cr)
                        max_t = max(max_t, ct)
                        has_valid_chars = True
                except Exception:
                    continue

            if not has_valid_chars:
                min_l, min_b, max_r, max_t = 0.0, 0.0, width, height

            span = RawPdfTextSpan(
                text=line_clean,
                bbox_pdf=(min_l, min_b, max_r, max_t),
                char_start=start_idx,
                char_end=end_idx,
            )

            blocks.append(
                RawPdfTextBlock(
                    text=line_clean,
                    bbox_pdf=(min_l, min_b, max_r, max_t),
                    spans=[span],
                    reading_sequence_idx=seq_idx,
                )
            )
            seq_idx += 1

        return blocks

    def _extract_images(
        self, page: pdfium.PdfPage, width: float, height: float
    ) -> List[RawPdfImage]:
        """Extract embedded image objects and their PDF bounding boxes."""
        images: List[RawPdfImage] = []
        img_idx = 0

        for obj in page.get_objects():
            obj_type = getattr(obj, "type", None)
            if obj_type == pdfium_c.FPDF_PAGEOBJ_IMAGE or "Image" in type(obj).__name__:
                try:
                    rect = obj.get_bounds()
                    img_l, img_b, img_r, img_t = float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])
                except Exception:
                    img_l, img_b, img_r, img_t = 0.0, 0.0, width, height

                width_px, height_px = int(abs(img_r - img_l)), int(abs(img_t - img_b))
                try:
                    meta = obj.get_image_metadata()
                    if meta.width > 0:
                        width_px = int(meta.width)
                    if meta.height > 0:
                        height_px = int(meta.height)
                except Exception:
                    pass

                images.append(
                    RawPdfImage(
                        image_index=img_idx,
                        bbox_pdf=(img_l, img_b, img_r, img_t),
                        width_px=max(1, width_px),
                        height_px=max(1, height_px),
                        mime_type="image/png",
                    )
                )
                img_idx += 1

        return images

    def _extract_links(self, page: pdfium.PdfPage) -> List[RawPdfLink]:
        """Extract URI links and internal page destination annotations."""
        links: List[RawPdfLink] = []
        try:
            for link in page.get_links():
                rect = link.get_rect()
                uri = link.get_url()
                target_p = link.get_target_page_index()
                links.append(
                    RawPdfLink(
                        uri=uri if uri else None,
                        target_page=target_p if target_p is not None else None,
                        bbox_pdf=(float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])),
                    )
                )
        except Exception:
            pass
        return links

    def render_page_image(self, page_index: int, dpi: int = 150) -> bytes:
        """Render page to PNG image bytes at target DPI for OCR processing."""
        if self._pdf is None:
            raise PdfInspectionError("Backend document is not open")
        page = self._pdf[page_index]
        scale = dpi / 72.0
        pil_image = page.render(scale=scale).to_pil()
        buf = io.BytesIO()
        pil_image.save(buf, format="PNG")
        return buf.getvalue()

    def close(self) -> None:
        if self._pdf is not None:
            self._pdf.close()
            self._pdf = None
