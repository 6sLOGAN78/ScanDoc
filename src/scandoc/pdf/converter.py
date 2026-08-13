"""
Native PDF Extractor and DocumentIR Assembler.

Converts raw PDF extraction streams into a strongly typed, normalized DocumentIR graph.
"""

import logging
from pathlib import Path
from typing import BinaryIO, Optional, Type, Union

from scandoc.models.blocks import BlockNode, FigureBlock, ImageRef, TextBlock, TextSpan
from scandoc.models.document import (
    DocumentIR,
    DocumentMetadata,
    DocumentStructure,
    Page,
    ReadingOrder,
)
from scandoc.models.geometry import BoundingBox, CoordOrigin, SizeUnit
from scandoc.models.provenance import ProcessingStage, Provenance
from scandoc.pdf.backend import BasePdfBackend, PyPdfium2Backend
from scandoc.pdf.inspector import PdfInspector
from scandoc.pdf.models import PdfInspectionResult
from scandoc.pdf.raw_models import RawPdfPageData, RawPdfTextBlock, RawPdfTextSpan

logger = logging.getLogger("scandoc.pdf.converter")


class NativePdfExtractor:
    """
    Format-specific native PDF extraction pipeline.
    
    Extracts text streams, font metadata, embedded images, page attributes,
    and converts PDF coordinates into a unified DocumentIR graph.
    """

    def __init__(self, backend_cls: Type[BasePdfBackend] = PyPdfium2Backend):
        self._backend_cls = backend_cls

    def extract(
        self,
        source: Union[str, Path, bytes, bytearray, BinaryIO],
        file_path: Optional[str] = None,
    ) -> DocumentIR:
        """
        Extract native PDF content and assemble a verified DocumentIR instance.
        
        Args:
            source: Input PDF path, bytes, or stream.
            file_path: Human-readable file label.
            
        Returns:
            DocumentIR instance containing extracted native document elements.
        """
        # Step 1: Execute Fast PDF Inspection
        inspection: PdfInspectionResult = PdfInspector.inspect(source, file_path=file_path)
        
        doc_id = f"doc-{Path(file_path).stem}" if file_path else f"doc-{hash(source) & 0xFFFFFFFF:08x}"
        doc_name = Path(file_path).name if file_path else "extracted_document.pdf"
        
        metadata = DocumentMetadata(
            id=doc_id,
            name=doc_name,
            mime_type="application/pdf",
            page_count=inspection.page_count,
            title=inspection.title,
            author=inspection.author,
            created_at=inspection.creation_date,
            mod_date=inspection.mod_date,
        )

        pages: list[Page] = []
        global_reading_sequence: list[str] = []
        body_block_ids: list[str] = []

        provenance = Provenance(
            provider="pypdfium2",
            stage=ProcessingStage.NATIVE_EXTRACTION,
            confidence=1.0,
        )

        # Step 2: Extract Page Data via Backend
        with self._backend_cls() as backend:
            backend.open(source)
            
            for page_index in range(inspection.page_count):
                raw_page: RawPdfPageData = backend.extract_page(page_index)
                
                page_blocks: list[BlockNode] = []
                
                # Convert Native Text Blocks
                for txt_idx, raw_txt in enumerate(raw_page.text_blocks):
                    block_id = f"p{page_index}-b{txt_idx}"
                    bbox_norm = self._convert_pdf_bbox(
                        raw_txt.bbox_pdf,
                        raw_page.width,
                        raw_page.height,
                        raw_page.rotation,
                        page_index,
                    )
                    
                    spans = [
                        TextSpan(
                            text=s.text,
                            start_char_idx=s.char_start,
                            end_char_idx=s.char_end,
                            bbox=self._convert_pdf_bbox(
                                s.bbox_pdf,
                                raw_page.width,
                                raw_page.height,
                                raw_page.rotation,
                                page_index,
                            ),
                            confidence=1.0,
                        )
                        for s in raw_txt.spans
                    ]
                    
                    txt_block = TextBlock(
                        id=block_id,
                        text=raw_txt.text,
                        bbox=bbox_norm,
                        spans=spans if spans else None,
                        reading_order_index=len(global_reading_sequence),
                        provenance=provenance,
                    )
                    page_blocks.append(txt_block)
                    global_reading_sequence.append(block_id)
                    body_block_ids.append(block_id)

                # Convert Embedded Image Figures
                for img_idx, raw_img in enumerate(raw_page.images):
                    fig_id = f"p{page_index}-fig{img_idx}"
                    bbox_norm = self._convert_pdf_bbox(
                        raw_img.bbox_pdf,
                        raw_page.width,
                        raw_page.height,
                        raw_page.rotation,
                        page_index,
                    )
                    
                    img_ref = ImageRef(
                        mime_type=raw_img.mime_type or "image/png",
                        width_px=raw_img.width_px,
                        height_px=raw_img.height_px,
                    )
                    
                    fig_block = FigureBlock(
                        id=fig_id,
                        image_ref=img_ref,
                        bbox=bbox_norm,
                        reading_order_index=len(global_reading_sequence),
                        provenance=provenance,
                    )
                    page_blocks.append(fig_block)
                    global_reading_sequence.append(fig_id)
                    body_block_ids.append(fig_id)

                page_obj = Page(
                    page_index=page_index,
                    width=raw_page.width,
                    height=raw_page.height,
                    rotation=raw_page.rotation,
                    unit=SizeUnit.POINTS,
                    blocks=page_blocks,
                    provenance=[provenance],
                )
                pages.append(page_obj)

        reading_order = ReadingOrder(sequence=global_reading_sequence)
        structure = DocumentStructure(body_block_ids=body_block_ids)

        doc_ir = DocumentIR(
            metadata=metadata,
            pages=pages,
            reading_order=reading_order,
            structure=structure,
        )

        logger.info(
            "Extracted native PDF '%s': pages=%d, blocks=%d",
            doc_name,
            len(pages),
            len(global_reading_sequence),
        )
        return doc_ir

    @staticmethod
    def _convert_pdf_bbox(
        bbox_pdf: tuple[float, float, float, float],
        page_width: float,
        page_height: float,
        rotation: int,
        page_index: int,
    ) -> BoundingBox:
        """
        Convert PDF point bounding box (left, bottom, right, top) to DocumentIR
        top-left origin normalized coordinates [left, top, right, bottom] (0.0 to 1.0),
        accounting for page rotation.
        """
        l_pdf, b_pdf, r_pdf, t_pdf = bbox_pdf
        
        # Ensure non-negative dimensions
        w = max(1.0, page_width)
        h = max(1.0, page_height)
        
        rot = rotation % 360

        if rot == 0:
            l_norm = l_pdf / w
            r_norm = r_pdf / w
            t_norm = (h - t_pdf) / h
            b_norm = (h - b_pdf) / h
        elif rot == 90:
            # 90 deg clockwise rotation
            l_norm = b_pdf / h
            r_norm = t_pdf / h
            t_norm = l_pdf / w
            b_norm = r_pdf / w
        elif rot == 180:
            l_norm = (w - r_pdf) / w
            r_norm = (w - l_pdf) / w
            t_norm = b_pdf / h
            b_norm = t_pdf / h
        elif rot == 270:
            l_norm = (h - t_pdf) / h
            r_norm = (h - b_pdf) / h
            t_norm = (w - r_pdf) / w
            b_norm = (w - l_pdf) / w
        else:
            l_norm = l_pdf / w
            r_norm = r_pdf / w
            t_norm = (h - t_pdf) / h
            b_norm = (h - b_pdf) / h

        # Clamp normalized coordinates to [0.0, 1.0] range
        l_final = max(0.0, min(1.0, l_norm))
        r_final = max(0.0, min(1.0, r_norm))
        t_final = max(0.0, min(1.0, t_norm))
        b_final = max(0.0, min(1.0, b_norm))

        # Enforce left <= right and top <= bottom
        if l_final > r_final:
            l_final, r_final = r_final, l_final
        if t_final > b_final:
            t_final, b_final = b_final, t_final

        return BoundingBox(
            left=round(l_final, 5),
            top=round(t_final, 5),
            right=round(r_final, 5),
            bottom=round(b_final, 5),
            page_index=page_index,
            coord_origin=CoordOrigin.TOP_LEFT,
            unit=SizeUnit.NORMALIZED,
            is_normalized=True,
        )
