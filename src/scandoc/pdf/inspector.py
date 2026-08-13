"""
Fast, render-free PDF inspector implementation for scanDOC.
"""

import logging
from pathlib import Path
from typing import BinaryIO, List, Optional, Union

import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_c

from scandoc.models.geometry import BoundingBox, CoordOrigin, SizeUnit
from scandoc.pdf.exceptions import (
    EmptyPdfError,
    EncryptedPdfError,
    MalformedPdfError,
    PdfInspectionError,
)
from scandoc.pdf.models import (
    DocumentCategory,
    ImageDetails,
    PageContentType,
    PageInspectionResult,
    PdfInspectionResult,
    PipelineSignals,
)

logger = logging.getLogger("scandoc.pdf.inspector")


class PdfInspector:
    """
    High-performance, render-free PDF inspection engine.
    
    Analyzes native text streams, page dimensions, rotation, embedded image objects,
    and metadata without rendering page images to raster buffers.
    """

    @classmethod
    def inspect(
        cls,
        source: Union[str, Path, bytes, bytearray, BinaryIO],
        file_path: Optional[str] = None,
    ) -> PdfInspectionResult:
        """
        Inspect a PDF document from file path, bytes buffer, or binary stream.
        
        Args:
            source: Path to PDF file, bytes buffer, or open binary stream.
            file_path: Optional human-readable filename for reporting.
            
        Returns:
            PdfInspectionResult containing structured metadata and pipeline signals.
            
        Raises:
            MalformedPdfError: If PDF structure is invalid or corrupt.
            EncryptedPdfError: If PDF is password protected.
            EmptyPdfError: If PDF has 0 pages.
            PdfInspectionError: For general inspection failures.
        """
        logger.debug("Starting PDF inspection for source: %s", file_path or type(source).__name__)
        
        file_size_bytes = 0
        input_file_path = file_path

        if isinstance(source, (str, Path)):
            path_obj = Path(source)
            if not path_obj.exists():
                raise PdfInspectionError(f"PDF file not found: {source}")
            input_file_path = str(path_obj.resolve())
            file_size_bytes = path_obj.stat().st_size
            pdf_input = input_file_path
        elif isinstance(source, (bytes, bytearray)):
            file_size_bytes = len(source)
            pdf_input = bytes(source)
        elif hasattr(source, "read"):
            content = source.read()
            file_size_bytes = len(content)
            pdf_input = content
        else:
            raise PdfInspectionError(f"Unsupported PDF input source type: {type(source)}")

        if file_size_bytes == 0:
            raise EmptyPdfError("Input PDF source is 0 bytes")

        try:
            pdf_doc = pdfium.PdfDocument(pdf_input)
        except pdfium.PdfiumError as e:
            err_msg = str(e).lower()
            if "password" in err_msg or "encrypted" in err_msg or "protection" in err_msg:
                logger.warning("PDF is encrypted or password-protected: %s", e)
                raise EncryptedPdfError("PDF is password-protected or encrypted") from e
            logger.error("Pdfium parsing failed for PDF: %s", e)
            raise MalformedPdfError(f"Malformed or unparseable PDF document: {e}") from e
        except Exception as e:
            logger.error("Failed to load PDF document: %s", e)
            raise MalformedPdfError(f"Failed to open PDF document: {e}") from e

        try:
            page_count = len(pdf_doc)
            if page_count == 0:
                raise EmptyPdfError("PDF contains 0 pages")

            # Read document metadata
            raw_meta = pdf_doc.get_metadata_dict()
            title = raw_meta.get("Title")
            author = raw_meta.get("Author")
            subject = raw_meta.get("Subject")
            creator = raw_meta.get("Creator")
            producer = raw_meta.get("Producer")
            creation_date = raw_meta.get("CreationDate")
            mod_date = raw_meta.get("ModDate")
            
            extra_meta = {
                k: v for k, v in raw_meta.items()
                if k not in ("Title", "Author", "Subject", "Creator", "Producer", "CreationDate", "ModDate")
            }

            pages_result: List[PageInspectionResult] = []
            scanned_pages_count = 0
            total_char_count = 0
            total_text_density = 0.0

            for page_index in range(page_count):
                page_res = cls._inspect_page(pdf_doc, page_index)
                pages_result.append(page_res)
                
                total_char_count += page_res.character_count
                total_text_density += page_res.text_density_ratio
                if page_res.content_type in (PageContentType.SCANNED_IMAGE_ONLY, PageContentType.EMPTY):
                    scanned_pages_count += 1

            # Classification & Signals
            scanned_page_ratio = round(scanned_pages_count / page_count, 4)
            avg_text_density = round(total_text_density / page_count, 4)

            category = cls._classify_document(pages_result, scanned_page_ratio)

            signals = PipelineSignals(
                recommended_fast_path=(category == DocumentCategory.DIGITALLY_GENERATED),
                has_native_text=(total_char_count > 20),
                ocr_suggested=(category in (DocumentCategory.SCANNED, DocumentCategory.IMAGE_ONLY, DocumentCategory.HYBRID)),
                vlm_suggested=(category == DocumentCategory.IMAGE_ONLY),
                is_encrypted=False,
                avg_text_density=avg_text_density,
                scanned_page_ratio=scanned_page_ratio,
            )

            result = PdfInspectionResult(
                file_path=input_file_path,
                file_size_bytes=file_size_bytes,
                page_count=page_count,
                title=title if title else None,
                author=author if author else None,
                subject=subject if subject else None,
                creator=creator if creator else None,
                producer=producer if producer else None,
                creation_date=creation_date if creation_date else None,
                mod_date=mod_date if mod_date else None,
                is_encrypted=False,
                category=category,
                pages=pages_result,
                signals=signals,
                extra_metadata=extra_meta,
            )
            
            logger.info(
                "Inspected PDF '%s': pages=%d, category=%s, fast_path=%s",
                input_file_path or "bytes",
                page_count,
                category.value,
                signals.recommended_fast_path,
            )
            return result

        finally:
            pdf_doc.close()

    @classmethod
    def _inspect_page(cls, pdf_doc: pdfium.PdfDocument, page_index: int) -> PageInspectionResult:
        """Inspect a single page using render-free pdfium page and textpage objects."""
        page = pdf_doc[page_index]
        width = float(page.get_width())
        height = float(page.get_height())
        rotation = int(page.get_rotation()) % 360

        # Native text stream inspection
        text_page = page.get_textpage()
        char_count = text_page.count_chars()
        full_text = text_page.get_text_bounded() if char_count > 0 else ""
        word_count = len(full_text.split())

        # Page objects image inspection
        images: List[ImageDetails] = []
        image_count = 0
        total_image_area = 0.0
        page_area = width * height if (width > 0 and height > 0) else 1.0

        for obj in page.get_objects():
            # FPDF_PAGEOBJ_IMAGE == 3 in pdfium
            obj_type = getattr(obj, "type", None)
            if obj_type == pdfium_c.FPDF_PAGEOBJ_IMAGE or "Image" in type(obj).__name__:
                image_count += 1
                try:
                    rect = obj.get_bounds()  # (left, bottom, right, top) in pdfium
                    img_l, img_b, img_r, img_t = float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])
                    img_w = abs(img_r - img_l)
                    img_h = abs(img_t - img_b)
                except Exception:
                    img_l, img_b, img_r, img_t = 0.0, 0.0, width, height
                    img_w, img_h = width, height

                img_area = img_w * img_h
                total_image_area += img_area

                width_px, height_px = 0, 0
                try:
                    meta = obj.get_image_metadata()
                    width_px = int(meta.width)
                    height_px = int(meta.height)
                except Exception:
                    pass

                if width_px <= 0:
                    width_px = int(img_w)
                if height_px <= 0:
                    height_px = int(img_h)

                width_in = img_w / 72.0 if img_w > 0 else 1.0
                height_in = img_h / 72.0 if img_h > 0 else 1.0
                h_dpi = round(width_px / width_in, 1) if width_in > 0 else None
                v_dpi = round(height_px / height_in, 1) if height_in > 0 else None

                cov_ratio = min(1.0, img_area / page_area)

                # Normalized BoundingBox calculation
                norm_l = max(0.0, min(1.0, img_l / width)) if width > 0 else 0.0
                norm_t = max(0.0, min(1.0, (height - img_t) / height)) if height > 0 else 0.0
                norm_r = max(0.0, min(1.0, img_r / width)) if width > 0 else 1.0
                norm_b = max(0.0, min(1.0, (height - img_b) / height)) if height > 0 else 1.0

                bbox = None
                if norm_l <= norm_r and norm_t <= norm_b:
                    bbox = BoundingBox(
                        left=norm_l,
                        top=norm_t,
                        right=norm_r,
                        bottom=norm_b,
                        page_index=page_index,
                        coord_origin=CoordOrigin.TOP_LEFT,
                        unit=SizeUnit.NORMALIZED,
                        is_normalized=True,
                    )

                images.append(
                    ImageDetails(
                        image_index=image_count - 1,
                        width_px=width_px,
                        height_px=height_px,
                        horizontal_dpi=h_dpi,
                        vertical_dpi=v_dpi,
                        page_coverage_ratio=round(cov_ratio, 4),
                        bbox=bbox,
                    )
                )

        combined_img_coverage = min(1.0, total_image_area / page_area)

        # Classify Page Content Type
        if char_count >= 50 and image_count == 0:
            content_type = PageContentType.DIGITAL_TEXT_ONLY
        elif char_count < 20 and image_count > 0:
            content_type = PageContentType.SCANNED_IMAGE_ONLY
        elif char_count >= 20 and image_count > 0:
            content_type = PageContentType.HYBRID
        else:
            content_type = PageContentType.EMPTY

        # Estimated text density ratio (relative to ~2,500 chars/page maximum capacity)
        text_density_ratio = min(1.0, round(char_count / 2500.0, 4))

        return PageInspectionResult(
            page_index=page_index,
            width=width,
            height=height,
            rotation=rotation,
            unit=SizeUnit.POINTS,
            content_type=content_type,
            character_count=char_count,
            word_count=word_count,
            text_density_ratio=text_density_ratio,
            has_native_text=(char_count > 0),
            has_images=(image_count > 0),
            image_count=image_count,
            images=images,
            image_coverage_ratio=round(combined_img_coverage, 4),
        )

    @classmethod
    def _classify_document(
        cls, pages: List[PageInspectionResult], scanned_page_ratio: float
    ) -> DocumentCategory:
        """Categorize document generation type based on aggregated page metrics."""
        total_pages = len(pages)
        if total_pages == 0:
            return DocumentCategory.IMAGE_ONLY

        digital_pages = sum(1 for p in pages if p.content_type == PageContentType.DIGITAL_TEXT_ONLY)
        scanned_pages = sum(1 for p in pages if p.content_type == PageContentType.SCANNED_IMAGE_ONLY)
        hybrid_pages = sum(1 for p in pages if p.content_type == PageContentType.HYBRID)
        
        avg_img_coverage = sum(p.image_coverage_ratio for p in pages) / total_pages

        if scanned_pages == total_pages and avg_img_coverage >= 0.70:
            return DocumentCategory.IMAGE_ONLY
        elif scanned_page_ratio >= 0.75:
            return DocumentCategory.SCANNED
        elif digital_pages == total_pages or (digital_pages + hybrid_pages == total_pages and avg_img_coverage < 0.35):
            return DocumentCategory.DIGITALLY_GENERATED
        else:
            return DocumentCategory.HYBRID
