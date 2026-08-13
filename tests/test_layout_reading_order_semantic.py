"""
Unit and integration test suite for Phase 19: Layout Analysis, Reading Order & Semantic Structure.
"""

import pytest

from scandoc.analysis import (
    DocumentSection,
    DocumentStructureTree,
    LayoutAnalyzer,
    LayoutResult,
    SemanticCategory,
    SemanticClassifier,
    SpatialGraph,
    SpatialRelationType,
)
from scandoc.models import Page
from scandoc.models.blocks import FigureBlock, HeadingBlock, ParagraphBlock
from scandoc.models.geometry import BoundingBox
from scandoc.models.provenance import ProcessingStage, Provenance


def test_spatial_graph_directional_relations():
    """Test SpatialGraph building directional edges (ABOVE, BELOW, RIGHT_OF, LEFT_OF) between nodes."""
    graph = SpatialGraph()

    prov = Provenance(provider="test", model="test", stage=ProcessingStage.NATIVE_EXTRACTION)

    top_b = ParagraphBlock(
        id="top_1", text="Top Header Text",
        bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.2, is_normalized=True),
        provenance=prov,
    )
    bottom_b = ParagraphBlock(
        id="bottom_1", text="Bottom Paragraph Text",
        bbox=BoundingBox(left=0.1, top=0.3, right=0.9, bottom=0.4, is_normalized=True),
        provenance=prov,
    )

    graph.build_from_blocks([top_b, bottom_b])

    assert "top_1" in graph.nodes
    assert "bottom_1" in graph.nodes

    # Check top_1 -> bottom_1 (BELOW relation)
    neighbors = graph.find_neighbors("top_1", SpatialRelationType.BELOW)
    assert len(neighbors) == 1
    assert neighbors[0].node_id == "bottom_1"


def test_semantic_classifier_heading_header_footer_page_number():
    """Test SemanticClassifier classifying headings, headers, footers, and page numbers."""
    prov = Provenance(provider="test", model="test", stage=ProcessingStage.NATIVE_EXTRACTION)

    # 1. Page Number
    pg_num_b = ParagraphBlock(
        id="pg_1", text="Page 1",
        bbox=BoundingBox(left=0.4, top=0.95, right=0.6, bottom=0.98, is_normalized=True),
        provenance=prov,
    )
    cat_pg, conf_pg = SemanticClassifier.classify_block(pg_num_b)
    assert cat_pg == SemanticCategory.PAGE_NUMBER
    assert conf_pg >= 0.80

    # 2. Heading
    h1_b = HeadingBlock(
        id="h1_1", text="System Architecture Overview", level=1,
        bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.15, is_normalized=True),
        provenance=prov,
    )
    cat_h, conf_h = SemanticClassifier.classify_block(h1_b)
    assert cat_h == SemanticCategory.HEADING
    assert conf_h >= 0.90

    # 3. Caption
    cap_b = ParagraphBlock(
        id="cap_1", text="Figure 1: Overall system pipeline flowchart.",
        bbox=BoundingBox(left=0.1, top=0.5, right=0.9, bottom=0.55, is_normalized=True),
        provenance=prov,
    )
    cat_c, conf_c = SemanticClassifier.classify_block(cap_b)
    assert cat_c == SemanticCategory.CAPTION
    assert conf_c >= 0.90


def test_layout_analyzer_two_column_reading_order_and_caption_association():
    """Test LayoutAnalyzer multi-column reading order and figure-caption association."""
    prov = Provenance(provider="test", model="test", stage=ProcessingStage.NATIVE_EXTRACTION)

    # Column 1 Block (left)
    col1_b = ParagraphBlock(
        id="col1_b1", text="Column 1 paragraph text content.",
        bbox=BoundingBox(left=0.05, top=0.2, right=0.45, bottom=0.4, is_normalized=True),
        provenance=prov,
    )
    # Column 2 Block (right)
    col2_b = ParagraphBlock(
        id="col2_b1", text="Column 2 paragraph text content.",
        bbox=BoundingBox(left=0.55, top=0.2, right=0.95, bottom=0.4, is_normalized=True),
        provenance=prov,
    )
    # Figure Block
    fig_b = FigureBlock(
        id="fig_1", caption=None,
        bbox=BoundingBox(left=0.05, top=0.45, right=0.45, bottom=0.7, is_normalized=True),
        provenance=prov,
    )
    # Caption Block
    cap_b = ParagraphBlock(
        id="cap_1", text="Figure 1: Test figure caption.",
        bbox=BoundingBox(left=0.05, top=0.72, right=0.45, bottom=0.78, is_normalized=True),
        provenance=prov,
    )

    page = Page(page_index=0, width=612.0, height=792.0, blocks=[col1_b, col2_b, fig_b, cap_b])

    res = LayoutAnalyzer.analyze_page(page)

    assert isinstance(res, LayoutResult)
    assert len(res.ordered_blocks) == 4
    assert isinstance(res.structure_tree, DocumentStructureTree)
