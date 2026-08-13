"""
Converter mapping FigureResult models into DocumentIR FigureBlock objects.
"""

from typing import Optional

from scandoc.models.blocks import CaptionBlock, FigureBlock
from scandoc.models.provenance import ProcessingStage, Provenance
from scandoc.providers.figures.models import FigureResult


def figure_result_to_document_ir(
    fig_result: FigureResult,
    target_figure_block: Optional[FigureBlock] = None,
) -> FigureBlock:
    """
    Convert FigureResult into DocumentIR FigureBlock model.
    
    Preserves bounding box, caption text, figure classification, and provenance metadata.
    """
    prov = Provenance(
        provider=fig_result.provider_id,
        model=fig_result.model_id,
        stage=ProcessingStage.POST_PROCESSING,
        confidence=fig_result.confidence,
    )

    if target_figure_block is not None:
        target_figure_block.bbox = fig_result.bbox
        target_figure_block.caption = fig_result.associated_caption_text
        target_figure_block.alt_text = fig_result.description
        target_figure_block.provenance = prov
        return target_figure_block

    return FigureBlock(
        id=fig_result.figure_id,
        bbox=fig_result.bbox,
        caption=fig_result.associated_caption_text,
        alt_text=fig_result.description,
        provenance=prov,
    )
