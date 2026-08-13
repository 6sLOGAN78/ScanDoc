"""
Unit and integration test suite for Phase 10: Reading Order & Document Structure Reconstruction.
"""

import uuid
import pytest

from scandoc.models import DocumentIR, DocumentMetadata, Page
from scandoc.models.blocks import (
    CaptionBlock,
    FigureBlock,
    HeadingBlock,
    ListBlock,
    ListItem,
    ParagraphBlock,
    TableBlock,
)
from scandoc.models.geometry import BoundingBox
from scandoc.models.provenance import ProcessingStage, Provenance
from scandoc.providers.layout.models import LayoutCategory, LayoutRegion, LayoutResult
from scandoc.structure import (
    DocumentHierarchy,
    DocumentHierarchyBuilder,
    ReadingOrderResult,
    XYCutReadingOrderEngine,
)


def create_prov():
    return Provenance(provider="test", stage=ProcessingStage.NATIVE_EXTRACTION)


def test_single_column_document_reading_order():
    """Test 1: Single-column document top-to-bottom reading order."""
    b1 = ParagraphBlock(id="p1", text="First Paragraph", bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.2, is_normalized=True), provenance=create_prov())
    b2 = ParagraphBlock(id="p2", text="Second Paragraph", bbox=BoundingBox(left=0.1, top=0.3, right=0.9, bottom=0.4, is_normalized=True), provenance=create_prov())
    b3 = ParagraphBlock(id="p3", text="Third Paragraph", bbox=BoundingBox(left=0.1, top=0.5, right=0.9, bottom=0.6, is_normalized=True), provenance=create_prov())

    page = Page(page_index=0, page_number=1, width=1000, height=1400, blocks=[b1, b2, b3])
    engine = XYCutReadingOrderEngine()
    result: ReadingOrderResult = engine.order_page_blocks(page)

    assert result.ordered_block_ids == ["p1", "p2", "p3"]
    # Verify native extraction order in page.blocks is PRESERVED!
    assert [b.id for b in page.blocks] == ["p1", "p2", "p3"]


def test_two_column_document_reading_order():
    """Test 2: Two-column paper reading order (Column 1 A->B->C then Column 2 D->E)."""
    # Column 1 (Left 0.1 to 0.45)
    b_a = ParagraphBlock(id="block_A", text="Col1 Top", bbox=BoundingBox(left=0.1, top=0.2, right=0.45, bottom=0.3, is_normalized=True), provenance=create_prov())
    b_b = ParagraphBlock(id="block_B", text="Col1 Mid", bbox=BoundingBox(left=0.1, top=0.35, right=0.45, bottom=0.5, is_normalized=True), provenance=create_prov())
    b_c = ParagraphBlock(id="block_C", text="Col1 Bot", bbox=BoundingBox(left=0.1, top=0.55, right=0.45, bottom=0.7, is_normalized=True), provenance=create_prov())

    # Column 2 (Right 0.55 to 0.9)
    b_d = ParagraphBlock(id="block_D", text="Col2 Top", bbox=BoundingBox(left=0.55, top=0.2, right=0.9, bottom=0.3, is_normalized=True), provenance=create_prov())
    b_e = ParagraphBlock(id="block_E", text="Col2 Bot", bbox=BoundingBox(left=0.55, top=0.35, right=0.9, bottom=0.5, is_normalized=True), provenance=create_prov())

    # Intentional interleaved extraction order
    page = Page(page_index=0, page_number=1, width=1000, height=1400, blocks=[b_a, b_d, b_b, b_e, b_c])
    engine = XYCutReadingOrderEngine()
    result = engine.order_page_blocks(page)

    # Expected: Column 1 (A -> B -> C) then Column 2 (D -> E)
    assert result.ordered_block_ids == ["block_A", "block_B", "block_C", "block_D", "block_E"]


def test_three_column_and_unequal_columns():
    """Test 3 & 4: Three-column layout and unequal column widths."""
    col1 = ParagraphBlock(id="c1", text="Col 1", bbox=BoundingBox(left=0.05, top=0.1, right=0.3, bottom=0.5, is_normalized=True), provenance=create_prov())
    col2 = ParagraphBlock(id="c2", text="Col 2", bbox=BoundingBox(left=0.35, top=0.1, right=0.6, bottom=0.5, is_normalized=True), provenance=create_prov())
    col3 = ParagraphBlock(id="c3", text="Col 3", bbox=BoundingBox(left=0.65, top=0.1, right=0.95, bottom=0.5, is_normalized=True), provenance=create_prov())

    page = Page(page_index=0, page_number=1, width=1200, height=800, blocks=[col3, col1, col2])
    engine = XYCutReadingOrderEngine()
    result = engine.order_page_blocks(page)

    assert result.ordered_block_ids == ["c1", "c2", "c3"]


def test_header_footer_and_title_sections():
    """Test 6, 7 & 8: Headers/footers and hierarchical section reconstruction."""
    header = ParagraphBlock(id="hdr", text="Running Header", bbox=BoundingBox(left=0.1, top=0.02, right=0.9, bottom=0.05, is_normalized=True), provenance=create_prov())
    h1 = HeadingBlock(id="h1", level=1, text="Introduction", bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.15, is_normalized=True), provenance=create_prov())
    p1 = ParagraphBlock(id="p1", text="Intro text...", bbox=BoundingBox(left=0.1, top=0.18, right=0.9, bottom=0.3, is_normalized=True), provenance=create_prov())
    h2 = HeadingBlock(id="h2", level=2, text="Background", bbox=BoundingBox(left=0.1, top=0.35, right=0.9, bottom=0.4, is_normalized=True), provenance=create_prov())
    p2 = ParagraphBlock(id="p2", text="Background details...", bbox=BoundingBox(left=0.1, top=0.42, right=0.9, bottom=0.6, is_normalized=True), provenance=create_prov())
    footer = ParagraphBlock(id="ftr", text="Page 1", bbox=BoundingBox(left=0.1, top=0.95, right=0.9, bottom=0.98, is_normalized=True), provenance=create_prov())

    page = Page(page_index=0, page_number=1, width=1000, height=1400, blocks=[header, h1, p1, h2, p2, footer])
    doc = DocumentIR(metadata=DocumentMetadata(id="doc1", name="Paper"), pages=[page])

    engine = XYCutReadingOrderEngine()
    ro_res = engine.order_page_blocks(page)
    assert ro_res.ordered_block_ids == ["hdr", "h1", "p1", "h2", "p2", "ftr"]

    # Test Section Hierarchy Construction
    hierarchy: DocumentHierarchy = engine.reconstruct_hierarchy(doc, reading_orders=[ro_res])
    assert len(hierarchy.root_nodes) == 2
    sec_preamble = hierarchy.root_nodes[0]
    assert "hdr" in sec_preamble.block_ids

    sec1 = hierarchy.root_nodes[1]
    assert sec1.title == "Introduction"
    assert "p1" in sec1.block_ids
    assert len(sec1.children) == 1

    subsec1 = sec1.children[0]
    assert subsec1.title == "Background"
    assert "p2" in subsec1.block_ids


def test_figure_and_caption_association():
    """Test 12: Figure and caption spatial relationship detection."""
    fig = FigureBlock(id="fig1", bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.4, is_normalized=True), provenance=create_prov())
    cap = CaptionBlock(id="cap1", text="Figure 1: Architecture Diagram", bbox=BoundingBox(left=0.1, top=0.42, right=0.9, bottom=0.46, is_normalized=True), provenance=create_prov())

    page = Page(page_index=0, page_number=1, width=1000, height=1400, blocks=[fig, cap])
    engine = XYCutReadingOrderEngine()
    res = engine.order_page_blocks(page)

    fig_item = next(it for it in res.items if it.block_id == "fig1")
    assert fig_item.metadata.get("associated_caption") == "cap1"


def test_table_as_spatial_block():
    """Test 13: Table treated as spatial block without cell destruction."""
    tbl = TableBlock(id="tbl1", num_rows=1, num_cols=1, cells=[], bbox=BoundingBox(left=0.1, top=0.2, right=0.9, bottom=0.5, is_normalized=True), provenance=create_prov())
    page = Page(page_index=0, page_number=1, width=1000, height=1400, blocks=[tbl])
    engine = XYCutReadingOrderEngine()
    res = engine.order_page_blocks(page)

    assert res.ordered_block_ids == ["tbl1"]


def test_empty_page_handling():
    """Test 20: Empty page returns empty ReadingOrderResult cleanly."""
    page = Page(page_index=0, page_number=1, width=1000, height=1400, blocks=[])
    engine = XYCutReadingOrderEngine()
    res = engine.order_page_blocks(page)

    assert res.ordered_block_ids == []
    assert res.items == []
