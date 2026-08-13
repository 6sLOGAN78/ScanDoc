"""
Converter mapping LayoutResult predictions into DocumentIR page blocks.
"""

import uuid
from typing import List, Optional

from scandoc.models import DocumentIR, DocumentMetadata, Page
from scandoc.models.blocks import (
    CaptionBlock,
    FigureBlock,
    FormulaBlock,
    HeadingBlock,
    ListBlock,
    ParagraphBlock,
    TableBlock,
    TextBlock,
)
from scandoc.models.geometry import BoundingBox
from scandoc.models.provenance import ProcessingStage, Provenance
from scandoc.providers.layout.models import LayoutRegion, LayoutResult
from scandoc.providers.layout.taxonomy import LayoutCategory


def layout_result_to_document_ir(
    layout_result: LayoutResult,
    target_doc: Optional[DocumentIR] = None,
) -> DocumentIR:
    """
    Convert visual LayoutResult predictions into initial DocumentIR blocks.
    
    Preserves predicted category, normalized bounding box, confidence, and provenance metadata.
    Does NOT modify reading order sequence or perform semantic table/formula parsing.
    """
    doc = target_doc or DocumentIR(
        metadata=DocumentMetadata(id=str(uuid.uuid4()), name="Document")
    )

    # Ensure page exists
    page_idx = layout_result.page_index
    while len(doc.pages) <= page_idx:
        p_idx = len(doc.pages)
        doc.pages.append(
            Page(
                page_index=p_idx,
                page_number=p_idx + 1,
                width=float(layout_result.image_width),
                height=float(layout_result.image_height),
                blocks=[],
            )
        )

    target_page = doc.pages[page_idx]
    if target_page.width <= 0:
        target_page.width = float(layout_result.image_width)
    if target_page.height <= 0:
        target_page.height = float(layout_result.image_height)

    for reg_idx, region in enumerate(layout_result.regions):
        prov = Provenance(
            provider=layout_result.provider_id,
            model=layout_result.model_id,
            stage=ProcessingStage.LAYOUT_ANALYSIS,
            confidence=region.confidence,
        )

        block = _create_block_from_layout_region(region, reg_idx, prov)
        target_page.blocks.append(block)

    return doc


def _create_block_from_layout_region(
    region: LayoutRegion,
    seq_idx: int,
    provenance: Provenance,
) -> TextBlock:
    """Instantiate appropriate DocumentIR block model based on LayoutCategory."""
    cat = region.category
    bbox = region.bbox
    block_id = f"layout_block_{seq_idx}"

    if cat == LayoutCategory.TITLE:
        return HeadingBlock(
            id=block_id,
            level=1,
            text="",
            bbox=bbox,
            provenance=provenance,
        )
    elif cat == LayoutCategory.HEADER:
        return HeadingBlock(
            id=block_id,
            level=2,
            text="",
            bbox=bbox,
            provenance=provenance,
        )
    elif cat in (LayoutCategory.PARAGRAPH, LayoutCategory.TEXT, LayoutCategory.FOOTER, LayoutCategory.PAGE_NUMBER):
        return ParagraphBlock(
            id=block_id,
            text="",
            bbox=bbox,
            provenance=provenance,
        )
    elif cat == LayoutCategory.LIST:
        return ListBlock(
            id=block_id,
            items=[],
            bbox=bbox,
            provenance=provenance,
        )
    elif cat == LayoutCategory.TABLE:
        return TableBlock(
            id=block_id,
            num_rows=1,
            num_cols=1,
            cells=[],
            bbox=bbox,
            provenance=provenance,
        )
    elif cat == LayoutCategory.FIGURE:
        return FigureBlock(
            id=block_id,
            bbox=bbox,
            provenance=provenance,
        )
    elif cat == LayoutCategory.FORMULA:
        return FormulaBlock(
            id=block_id,
            latex_expression="",
            bbox=bbox,
            provenance=provenance,
        )
    elif cat == LayoutCategory.CAPTION:
        return CaptionBlock(
            id=block_id,
            text="",
            bbox=bbox,
            provenance=provenance,
        )
    else:
        return ParagraphBlock(
            id=block_id,
            text="",
            bbox=bbox,
            provenance=provenance,
        )
