"""
Recursive XY-Cut and geometric column-clustering Reading Order Engine implementation.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple

from scandoc.models import DocumentIR, Page
from scandoc.models.blocks import CaptionBlock, FigureBlock, TableBlock, TextBlock
from scandoc.models.provenance import ProcessingStage, Provenance
from scandoc.providers.layout.models import LayoutResult
from scandoc.structure.base import BaseReadingOrderEngine
from scandoc.structure.hierarchy import DocumentHierarchyBuilder
from scandoc.structure.models import (
    DocumentHierarchy,
    ReadingOrderItem,
    ReadingOrderResult,
)

logger = logging.getLogger("scandoc.structure.xy_cut")


class XYCutReadingOrderEngine(BaseReadingOrderEngine):
    """
    Deterministic Recursive XY-Cut & Column Clustering Reading Order Engine.
    
    Groups page blocks into spatial columns and orders text top-to-bottom within each column.
    Preserves original native extraction order in Page.blocks while returning ordered IDs.
    """

    def __init__(self, column_gap_threshold: float = 0.05):
        self._column_gap_threshold = column_gap_threshold

    @property
    def engine_id(self) -> str:
        return "xy_cut_reading_order"

    def order_page_blocks(
        self,
        page: Page,
        layout_result: Optional[LayoutResult] = None,
    ) -> ReadingOrderResult:
        start_time = time.perf_counter()

        if not page.blocks:
            return ReadingOrderResult(
                ordered_block_ids=[],
                items=[],
                algorithm_name=self.engine_id,
                page_index=page.page_index,
                processing_time_ms=0.0,
            )

        # Step 1: Extract Blocks & Coordinates
        blocks = list(page.blocks)

        # Step 2: Multi-Column Partitioning & Clustering
        columns = self._partition_into_columns(blocks)

        # Step 3: Sort Blocks Intra-Column Top-to-Bottom
        ordered_items: List[ReadingOrderItem] = []
        ordered_ids: List[str] = []

        seq_counter = 0
        for col_idx, col_blocks in enumerate(columns):
            # Sort top to bottom by top coordinate
            col_blocks_sorted = sorted(col_blocks, key=lambda b: (b.bbox.top, b.bbox.left))

            for block in col_blocks_sorted:
                category_name = block.__class__.__name__.replace("Block", "").lower()
                meta: Dict[str, str] = {
                    "column": str(col_idx),
                    "top": str(round(block.bbox.top, 4)),
                    "left": str(round(block.bbox.left, 4)),
                }

                # Check figure/caption spatial relationship across all page blocks
                caption_rel = self._find_caption_relationship(block, blocks)
                if caption_rel:
                    meta["associated_caption"] = caption_rel

                item = ReadingOrderItem(
                    block_id=block.id,
                    sequence_index=seq_counter,
                    column_index=col_idx,
                    category=category_name,
                    confidence=1.0,
                    metadata=meta,
                )
                ordered_items.append(item)
                ordered_ids.append(block.id)
                seq_counter += 1

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        prov = Provenance(
            provider=self.engine_id,
            model="RecursiveXYCut-v1",
            stage=ProcessingStage.READING_ORDER,
            confidence=1.0,
        )

        return ReadingOrderResult(
            ordered_block_ids=ordered_ids,
            items=ordered_items,
            algorithm_name=self.engine_id,
            page_index=page.page_index,
            processing_time_ms=round(elapsed_ms, 2),
            provenance=prov,
        )

    def _partition_into_columns(self, blocks: List[TextBlock]) -> List[List[TextBlock]]:
        """
        Group page blocks into vertical columns based on horizontal bounds.
        """
        if len(blocks) <= 1:
            return [blocks]

        # Calculate bounding boxes
        sorted_by_left = sorted(blocks, key=lambda b: (b.bbox.left, b.bbox.top))
        columns: List[List[TextBlock]] = []

        for block in sorted_by_left:
            placed = False
            b_left, b_right = block.bbox.left, block.bbox.right
            b_width = max(0.01, b_right - b_left)

            # Full-width spans (like titles or header/footers) form their own single-block columns
            if b_width >= 0.75:
                columns.append([block])
                continue

            for col in columns:
                # Calculate column horizontal bounds
                col_left = min(b.bbox.left for b in col)
                col_right = max(b.bbox.right for b in col)

                # Check horizontal overlap
                overlap_left = max(b_left, col_left)
                overlap_right = min(b_right, col_right)
                overlap = max(0.0, overlap_right - overlap_left)

                if overlap > 0.3 * b_width or abs(b_left - col_left) < self._column_gap_threshold:
                    col.append(block)
                    placed = True
                    break

            if not placed:
                columns.append([block])

        # Sort columns left-to-right by minimum left coordinate
        columns_sorted = sorted(columns, key=lambda col: min(b.bbox.left for b in col))
        return columns_sorted

    def _find_caption_relationship(self, block: TextBlock, col_blocks: List[TextBlock]) -> Optional[str]:
        """Check if block is a figure/table with an adjacent caption block."""
        if not isinstance(block, (FigureBlock, TableBlock)):
            return None

        b_top, b_bottom = block.bbox.top, block.bbox.bottom

        for other in col_blocks:
            if isinstance(other, CaptionBlock):
                o_top, o_bottom = other.bbox.top, other.bbox.bottom
                if abs(o_top - b_bottom) < 0.08 or abs(b_top - o_bottom) < 0.08:
                    return other.id

        return None

    def reconstruct_hierarchy(
        self,
        doc: DocumentIR,
        reading_orders: Optional[List[ReadingOrderResult]] = None,
    ) -> DocumentHierarchy:
        """Build hierarchical document section tree from ordered document blocks."""
        return DocumentHierarchyBuilder.build_hierarchy(doc, reading_orders=reading_orders)
