"""
AgentDocumentInspector analyzing document characteristics, native text density, scan likelihood, and page complexity.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Union

from scandoc.formats.detector import FormatDetector
from scandoc.pdf.inspector import PdfInspector
from scandoc.pdf.models import DocumentCategory

logger = logging.getLogger("scandoc.agent.inspector")


class PageCharacteristics:
    """
    Per-page structural characteristics container.
    """
    def __init__(
        self,
        page_index: int,
        native_text_ratio: float = 0.0,
        scan_probability: float = 0.0,
        image_density: float = 0.0,
        vector_density: float = 0.0,
        has_tables: bool = False,
        has_figures: bool = False,
        has_formulas: bool = False,
    ):
        self.page_index = page_index
        self.native_text_ratio = native_text_ratio
        self.scan_probability = scan_probability
        self.image_density = image_density
        self.vector_density = vector_density
        self.has_tables = has_tables
        self.has_figures = has_figures
        self.has_formulas = has_formulas


class DocumentCharacteristics:
    """
    Document-level structural inspection metrics.
    """
    def __init__(
        self,
        format_name: str,
        num_pages: int,
        classification: DocumentCategory,
        pages: List[PageCharacteristics],
    ):
        self.format_name = format_name
        self.num_pages = num_pages
        self.classification = classification
        self.pages = pages


class AgentDocumentInspector:
    """
    Document inspection engine producing quantitative page metrics for deterministic agent planning.
    """

    @classmethod
    def inspect_document(cls, source: Union[str, Path, bytes]) -> DocumentCharacteristics:
        """
        Inspect document source and return DocumentCharacteristics.
        """
        fmt = FormatDetector.detect(source)
        fmt_name = fmt.detected_format.lower()

        if fmt_name == "pdf" and isinstance(source, (str, Path)):
            pdf_ins = PdfInspector.inspect(source)
            cls_type = pdf_ins.document_classification

            page_chars: List[PageCharacteristics] = []
            for p_info in pdf_ins.pages:
                text_density = p_info.native_text_density
                scan_prob = 1.0 if p_info.content_type.value in ("scanned", "image_only") else (0.0 if text_density > 0.8 else 0.5)
                img_density = 0.8 if len(p_info.embedded_images) > 0 else 0.0

                page_chars.append(
                    PageCharacteristics(
                        page_index=p_info.page_number - 1,
                        native_text_ratio=text_density,
                        scan_probability=scan_prob,
                        image_density=img_density,
                        has_tables=(p_info.table_indicator_score > 0.4),
                        has_figures=(len(p_info.embedded_images) > 0),
                    )
                )

            return DocumentCharacteristics(
                format_name="pdf",
                num_pages=pdf_ins.page_count,
                classification=cls_type,
                pages=page_chars,
            )

        # Default fallback for images, text, docx, html
        is_scanned = fmt_name in ("png", "jpg", "jpeg", "webp", "tiff")
        page_char = PageCharacteristics(
            page_index=0,
            native_text_ratio=0.0 if is_scanned else 1.0,
            scan_probability=1.0 if is_scanned else 0.0,
            image_density=1.0 if is_scanned else 0.0,
        )

        return DocumentCharacteristics(
            format_name=fmt_name,
            num_pages=1,
            classification=DocumentCategory.SCANNED if is_scanned else DocumentCategory.DIGITALLY_GENERATED,
            pages=[page_char],
        )
