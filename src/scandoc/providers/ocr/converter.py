"""
Converter mapping OCRResult objects into DocumentIR document graphs.
"""

from typing import List, Optional

from scandoc.models.blocks import BlockNode, TextBlock
from scandoc.models.document import (
    DocumentIR,
    DocumentMetadata,
    DocumentStructure,
    Page,
    ReadingOrder,
)
from scandoc.models.geometry import SizeUnit
from scandoc.models.provenance import ProcessingStage, Provenance
from scandoc.providers.ocr.models import OCRResult


def ocr_result_to_document_ir(
    ocr_result: OCRResult,
    page_index: int = 0,
    doc_id: Optional[str] = None,
    doc_name: Optional[str] = None,
) -> DocumentIR:
    """
    Convert an OCRResult into a verified DocumentIR instance.
    
    Args:
        ocr_result: The OCRResult object produced by an BaseOcrProvider.
        page_index: Target 0-indexed page sequence number.
        doc_id: Optional document ID override.
        doc_name: Optional human-readable document name.
        
    Returns:
        DocumentIR graph containing extracted OCR text blocks.
    """
    effective_id = doc_id or f"doc-ocr-{hash(ocr_result.full_text) & 0xFFFFFFFF:08x}"
    effective_name = doc_name or f"ocr_page_{page_index}.png"

    metadata = DocumentMetadata(
        id=effective_id,
        name=effective_name,
        mime_type="image/png",
        page_count=page_index + 1,
    )

    blocks: List[BlockNode] = []
    reading_sequence: List[str] = []
    body_block_ids: List[str] = []

    for reg in ocr_result.regions:
        block_id = f"p{page_index}-ocr-{reg.region_idx}"
        
        prov = Provenance(
            provider=ocr_result.provider_id,
            model=ocr_result.model_id,
            confidence=reg.confidence,
            stage=ProcessingStage.OCR,
        )

        txt_block = TextBlock(
            id=block_id,
            text=reg.text,
            bbox=reg.bbox,
            polygon=reg.polygon,
            reading_order_index=reg.region_idx,
            provenance=prov,
        )
        blocks.append(txt_block)
        reading_sequence.append(block_id)
        body_block_ids.append(block_id)

    page = Page(
        page_index=page_index,
        width=float(ocr_result.image_width),
        height=float(ocr_result.image_height),
        unit=SizeUnit.PIXELS,
        blocks=blocks,
    )

    return DocumentIR(
        metadata=metadata,
        pages=[page],
        reading_order=ReadingOrder(sequence=reading_sequence),
        structure=DocumentStructure(body_block_ids=body_block_ids),
    )
