"""
Deterministic spatial caption association engine linking caption text to adjacent figures.
"""

import logging
from typing import Any, List, Optional

from scandoc.models.blocks import CaptionBlock, FigureBlock
from scandoc.providers.figures.models import FigureResult

logger = logging.getLogger("scandoc.providers.figures.caption")


class CaptionAssociator:
    """
    Associates caption blocks (from native PDF, OCR, or layout predictions) with figure regions based on spatial proximity.
    """

    @classmethod
    def associate_captions(
        cls,
        figures: List[FigureResult],
        page_blocks: List[Any],
        max_distance: float = 0.08,
    ) -> List[FigureResult]:
        """
        Associate caption text blocks with figure regions based on spatial vertical distance.
        
        Args:
            figures: List of FigureResult objects.
            page_blocks: List of DocumentIR page blocks or LayoutRegions.
            max_distance: Maximum vertical gap (in normalized units) for caption association.
            
        Returns:
            Updated list of FigureResult objects with caption IDs and texts populated.
        """
        if not figures or not page_blocks:
            return figures

        # Filter caption blocks
        captions: List[tuple[str, str, float, float]] = []
        for block in page_blocks:
            is_cap = False
            b_id = getattr(block, "id", None) or getattr(block, "region_idx", "cap_0")
            b_text = getattr(block, "text", "")
            bbox = getattr(block, "bbox", None)

            if isinstance(block, CaptionBlock):
                is_cap = True
            elif hasattr(block, "category") and getattr(block, "category", "") == "caption":
                is_cap = True

            if is_cap and bbox is not None:
                captions.append((str(b_id), b_text, bbox.top, bbox.bottom))

        if not captions:
            return figures

        updated_figures: List[FigureResult] = []

        for fig in figures:
            if fig.bbox is None:
                updated_figures.append(fig)
                continue

            f_top, f_bottom = fig.bbox.top, fig.bbox.bottom

            best_cap_id = None
            best_cap_text = None
            min_dist = float("inf")

            for cap_id, cap_text, c_top, c_bottom in captions:
                # Calculate vertical distance between figure and caption (above or below)
                dist_below = abs(c_top - f_bottom)
                dist_above = abs(f_top - c_bottom)
                dist = min(dist_below, dist_above)

                if dist < min_dist and dist <= max_distance:
                    min_dist = dist
                    best_cap_id = cap_id
                    best_cap_text = cap_text

            if best_cap_id is not None:
                fig_copy = fig.model_copy(
                    update={
                        "associated_caption_id": best_cap_id,
                        "associated_caption_text": best_cap_text,
                    }
                )
                updated_figures.append(fig_copy)
            else:
                updated_figures.append(fig)

        return updated_figures
