"""
LayoutAnalyzer unifying native geometry, spatial graphs, reading order partitioning, and semantic structure trees.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from scandoc.analysis.semantic_classifier import SemanticClassifier
from scandoc.analysis.spatial_graph import SpatialGraph, SpatialNode
from scandoc.analysis.taxonomy import SemanticCategory, SpatialRelationType
from scandoc.analysis.tree import DocumentSection, DocumentStructureTree
from scandoc.models import DocumentIR, Page
from scandoc.models.blocks import HeadingBlock, ListBlock, CaptionBlock
from scandoc.models.geometry import BoundingBox
from scandoc.structure.xy_cut_engine import XYCutReadingOrderEngine
import re

logger = logging.getLogger("scandoc.analysis.layout_analyzer")


class LayoutResult:
    """Container for page layout analysis outcome."""
    def __init__(
        self,
        page_index: int,
        spatial_graph: SpatialGraph,
        ordered_blocks: List[Any],
        categories: Dict[str, Tuple[SemanticCategory, float]],
        structure_tree: DocumentStructureTree,
    ):
        self.page_index = page_index
        self.spatial_graph = spatial_graph
        self.ordered_blocks = ordered_blocks
        self.categories = categories
        self.structure_tree = structure_tree


class LayoutAnalyzer:
    """
    Provider-independent Layout Analysis engine.
    Constructs spatial graphs, computes multi-column reading order, classifies blocks, and builds document structure trees.
    """

    @classmethod
    def analyze_page(
        cls,
        page: Page,
        page_width: float = 612.0,
        page_height: float = 792.0,
    ) -> LayoutResult:
        """
        Analyze page layout, construct spatial graph, determine multi-column reading order, and build structure tree.
        """
        blocks = list(page.blocks)

        # 1. Build Spatial Graph
        graph = SpatialGraph()
        graph.build_from_blocks(blocks, page_width=page_width, page_height=page_height)

        # 2. Semantic Block Classification
        categories: Dict[str, Tuple[SemanticCategory, float]] = {}
        for b in blocks:
            b_id = getattr(b, "id", "b_unknown")
            cat, conf = SemanticClassifier.classify_block(b, page_height=page_height, page_width=page_width)
            categories[b_id] = (cat, conf)

        # 3. Multi-Column Reading Order Determination via XY-Cut Engine
        ordered_blocks_raw = cls._compute_reading_order(blocks, page_width=page_width, page_height=page_height)
        
        # 3.5 Mutate text blocks into HeadingBlock / ParagraphBlock based on semantics
        ordered_blocks = []
        for b in ordered_blocks_raw:
            b_id = getattr(b, "id", "b_unknown")
            cat, _ = categories.get(b_id, (SemanticCategory.UNKNOWN, 0.0))
            
            if type(b).__name__.lower() == "textblock":
                text = getattr(b, "text", "")
                
                if cat == SemanticCategory.HEADING:
                    level = 1
                    if re.match(r"^(\d+\.\d+\.\d+)", text):
                        level = 3
                    elif re.match(r"^(\d+\.\d+)", text):
                        level = 2
                    elif text.istitle() and len(text) > 3:
                        level = 2
                    elif text.isupper() and len(text) > 3:
                        level = 2
                    if re.match(r"^(Abstract|References|Conclusion|Introduction)", text, re.IGNORECASE):
                        level = 1
                        
                    hb = HeadingBlock(
                        id=b.id,
                        bbox=b.bbox,
                        polygon=b.polygon,
                        reading_order_index=b.reading_order_index,
                        provenance=b.provenance,
                        text=text,
                        level=level
                    )
                    ordered_blocks.append(hb)
                else:
                    from scandoc.models.blocks import ParagraphBlock
                    pb = ParagraphBlock(
                        id=b.id,
                        bbox=b.bbox,
                        polygon=b.polygon,
                        reading_order_index=b.reading_order_index,
                        provenance=b.provenance,
                        text=text
                    )
                    ordered_blocks.append(pb)
            else:
                ordered_blocks.append(b)

        # 4. Caption Association (Linking Figure 1: ... captions to figures)
        cls._associate_captions(ordered_blocks, graph, categories)

        # 5. Build Document Structure Tree
        tree = cls._build_structure_tree(ordered_blocks, categories)

        return LayoutResult(
            page_index=page.page_index,
            spatial_graph=graph,
            ordered_blocks=ordered_blocks,
            categories=categories,
            structure_tree=tree,
        )

    @classmethod
    def _compute_reading_order(
        cls, blocks: List[Any], page_width: float, page_height: float
    ) -> List[Any]:
        """
        Compute reading order using XYCutReadingOrderEngine multi-column partitioning.
        """
        if not blocks:
            return []

        dummy_page = Page(page_index=0, width=page_width, height=page_height, blocks=blocks)
        xy_engine = XYCutReadingOrderEngine()
        ro_res = xy_engine.order_page_blocks(dummy_page)

        block_map = {getattr(b, "id", f"b_{i}"): b for i, b in enumerate(blocks)}
        ordered = []
        for b_id in ro_res.ordered_block_ids:
            if b_id in block_map:
                ordered.append(block_map[b_id])

        if len(ordered) == len(blocks):
            return ordered

        # Fallback sorting if XY-cut returns partial order
        return sorted(blocks, key=lambda b: (b.bbox.top if b.bbox else 0.0, b.bbox.left if b.bbox else 0.0))

    @classmethod
    def _associate_captions(
        cls,
        blocks: List[Any],
        graph: SpatialGraph,
        categories: Dict[str, Tuple[SemanticCategory, float]],
    ) -> None:
        """
        Associate caption text blocks with adjacent figure or table blocks based on spatial proximity.
        """
        for b in blocks:
            b_id = getattr(b, "id", "")
            cat, _ = categories.get(b_id, (SemanticCategory.UNKNOWN, 0.0))

            if cat == SemanticCategory.CAPTION:
                # Find adjacent figure or table neighbors in SpatialGraph
                neighbors = graph.find_neighbors(b_id)
                for n in neighbors:
                    if n.category in (SemanticCategory.FIGURE, SemanticCategory.TABLE):
                        # Attach caption association metadata to block
                        if hasattr(n.payload, "caption"):
                            n.payload.caption = getattr(b, "text", "")

    @classmethod
    def _build_structure_tree(
        cls,
        ordered_blocks: List[Any],
        categories: Dict[str, Tuple[SemanticCategory, float]],
    ) -> DocumentStructureTree:
        """
        Build hierarchical DocumentStructureTree from ordered blocks.
        """
        root_sections: List[DocumentSection] = []
        current_section = DocumentSection(section_id="sec_root", heading_text="Document Body", level=1)
        root_sections.append(current_section)

        for b in ordered_blocks:
            b_id = getattr(b, "id", "")
            cat, _ = categories.get(b_id, (SemanticCategory.UNKNOWN, 0.0))

            if cat == SemanticCategory.HEADING or type(b).__name__.lower() == "headingblock":
                level = getattr(b, "level", 1)
                text = getattr(b, "text", "Section")
                new_sec = DocumentSection(section_id=f"sec_{b_id}", heading_text=text, level=level)
                root_sections.append(new_sec)
                current_section = new_sec
            else:
                current_section.blocks.append(b)

        return DocumentStructureTree(title=root_sections[0].heading_text, sections=root_sections)
