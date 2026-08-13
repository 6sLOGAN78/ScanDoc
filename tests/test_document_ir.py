"""
Comprehensive unit test suite for scanDOC DocumentIR primitives and validation rules.
"""

import json
import pytest
from pydantic import ValidationError

from scandoc.core import (
    DocumentIR,
    DocumentMetadata,
    Page,
    ReadingOrder,
    BoundingBox,
    Point2D,
    CoordOrigin,
    SizeUnit,
    Provenance,
    ProcessingStage,
    BlockType,
    TextBlock,
    HeadingBlock,
    ParagraphBlock,
    ListBlock,
    ListItem,
    TableBlock,
    TableCell,
    FigureBlock,
    ImageRef,
    FormulaBlock,
    FormulaFormat,
    CaptionBlock,
    TextSpan,
)


def test_minimal_document():
    """Test building a minimal DocumentIR instance with zero pages."""
    meta = DocumentMetadata(
        id="doc-001",
        name="minimal.pdf",
        mime_type="application/pdf",
        page_count=0,
    )
    doc = DocumentIR(metadata=meta)
    assert doc.metadata.id == "doc-001"
    assert doc.metadata.name == "minimal.pdf"
    assert len(doc.pages) == 0
    assert len(doc.reading_order.sequence) == 0


def test_multi_page_document():
    """Test building a multi-page DocumentIR instance."""
    meta = DocumentMetadata(id="doc-002", name="multi_page.pdf", page_count=2)
    
    page0 = Page(
        page_index=0,
        width=612.0,
        height=792.0,
        blocks=[
            TextBlock(
                id="block-p0-1",
                text="Page 1 Text",
                bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.2, page_index=0),
            )
        ],
    )
    page1 = Page(
        page_index=1,
        width=612.0,
        height=792.0,
        blocks=[
            TextBlock(
                id="block-p1-1",
                text="Page 2 Text",
                bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.2, page_index=1),
            )
        ],
    )
    
    doc = DocumentIR(
        metadata=meta,
        pages=[page0, page1],
        reading_order=ReadingOrder(sequence=["block-p0-1", "block-p1-1"]),
    )
    assert len(doc.pages) == 2
    assert doc.pages[0].page_index == 0
    assert doc.pages[1].page_index == 1
    assert len(doc.all_blocks()) == 2
    assert doc.get_block("block-p0-1") is not None
    assert doc.get_block("block-p1-1") is not None


def test_text_and_paragraph_blocks():
    """Test TextBlock, ParagraphBlock, and TextSpan."""
    span1 = TextSpan(text="Hello", start_char_idx=0, end_char_idx=5)
    span2 = TextSpan(text="World", start_char_idx=6, end_char_idx=11)
    
    txt_block = TextBlock(
        id="txt-1",
        text="Hello World",
        bbox=BoundingBox(left=0.0, top=0.0, right=0.5, bottom=0.1),
        spans=[span1, span2],
    )
    assert txt_block.block_type == BlockType.TEXT
    assert txt_block.text == "Hello World"
    assert len(txt_block.spans) == 2

    para_block = ParagraphBlock(
        id="para-1",
        text="Hello World Paragraph",
        bbox=BoundingBox(left=0.0, top=0.1, right=0.5, bottom=0.3),
        child_text_ids=["txt-1"],
    )
    assert para_block.block_type == BlockType.PARAGRAPH
    assert para_block.child_text_ids == ["txt-1"]


def test_heading_blocks():
    """Test HeadingBlock levels (1 to 6) and validation."""
    h1 = HeadingBlock(
        id="h-1",
        text="Introduction",
        level=1,
        bbox=BoundingBox(left=0.0, top=0.0, right=1.0, bottom=0.1),
    )
    assert h1.level == 1
    assert h1.block_type == BlockType.HEADING

    with pytest.raises(ValidationError):
        HeadingBlock(
            id="h-invalid",
            text="Invalid Heading Level",
            level=7,  # Level must be <= 6
            bbox=BoundingBox(left=0.0, top=0.0, right=1.0, bottom=0.1),
        )


def test_bounding_boxes_and_geometry_validation():
    """Test BoundingBox geometry, origins, and validation rules."""
    bbox = BoundingBox(
        left=0.1,
        top=0.2,
        right=0.8,
        bottom=0.9,
        page_index=0,
        coord_origin=CoordOrigin.TOP_LEFT,
        unit=SizeUnit.NORMALIZED,
        is_normalized=True,
    )
    assert bbox.width == pytest.approx(0.7)
    assert bbox.height == pytest.approx(0.7)
    assert bbox.area == pytest.approx(0.49)
    assert bbox.to_tuple() == (0.1, 0.2, 0.8, 0.9)

    # Test left > right validation error
    with pytest.raises(ValidationError):
        BoundingBox(left=0.9, top=0.2, right=0.1, bottom=0.9)

    # Test top > bottom validation error
    with pytest.raises(ValidationError):
        BoundingBox(left=0.1, top=0.9, right=0.8, bottom=0.2)

    # Test out-of-bounds normalized coordinate error
    with pytest.raises(ValidationError):
        BoundingBox(left=-0.5, top=0.0, right=0.8, bottom=0.9, is_normalized=True)


def test_polygons():
    """Test polygon point coordinates."""
    poly = [Point2D(x=0.1, y=0.1), Point2D(x=0.9, y=0.1), Point2D(x=0.9, y=0.5)]
    block = TextBlock(
        id="poly-1",
        text="Poly text",
        bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.5),
        polygon=poly,
    )
    assert len(block.polygon) == 3
    assert block.polygon[0].x == 0.1
    assert block.polygon[1].y == 0.1


def test_provenance():
    """Test Provenance tracking attributes and confidence validation."""
    prov = Provenance(
        provider="rapidocr",
        model="PP-OCRv4",
        confidence=0.96,
        stage=ProcessingStage.OCR,
        source_ref="stream_10",
        version="1.2.0",
        timestamp="2026-08-14T00:00:00Z",
    )
    assert prov.provider == "rapidocr"
    assert prov.confidence == 0.96
    assert prov.stage == ProcessingStage.OCR

    with pytest.raises(ValidationError):
        Provenance(provider="test", confidence=1.5)  # Confidence > 1.0 invalid


def test_reading_order():
    """Test reading order sequence validation."""
    meta = DocumentMetadata(id="doc-ro", name="ro.pdf")
    page = Page(
        page_index=0,
        width=100.0,
        height=100.0,
        blocks=[
            TextBlock(id="b1", text="First", bbox=BoundingBox(left=0, top=0, right=1, bottom=0.1)),
            TextBlock(id="b2", text="Second", bbox=BoundingBox(left=0, top=0.1, right=1, bottom=0.2)),
        ],
    )
    doc = DocumentIR(
        metadata=meta,
        pages=[page],
        reading_order=ReadingOrder(sequence=["b1", "b2"]),
    )
    assert doc.reading_order.sequence == ["b1", "b2"]

    # Test reading order referencing non-existent block ID
    with pytest.raises(ValidationError):
        DocumentIR(
            metadata=meta,
            pages=[page],
            reading_order=ReadingOrder(sequence=["b1", "non-existent-id"]),
        )


def test_tables_and_merged_cells():
    """Test TableBlock structure, cells, and row/column spans."""
    cell1 = TableCell(cell_id="c1", row_index=0, col_index=0, row_span=1, col_span=2, is_header=True, text="Header Spanned")
    cell2 = TableCell(cell_id="c2", row_index=1, col_index=0, row_span=1, col_span=1, is_header=False, text="Data 1")
    cell3 = TableCell(cell_id="c3", row_index=1, col_index=1, row_span=1, col_span=1, is_header=False, text="Data 2")

    table = TableBlock(
        id="table-1",
        num_rows=2,
        num_cols=2,
        cells=[cell1, cell2, cell3],
        caption="Sample Table",
        bbox=BoundingBox(left=0.1, top=0.2, right=0.9, bottom=0.8),
    )
    assert table.num_rows == 2
    assert table.num_cols == 2
    assert table.cells[0].col_span == 2
    assert table.caption == "Sample Table"


def test_table_cell_validation():
    """Test invalid table cell spans or grid bounds."""
    # Invalid row_index exceeding num_rows
    with pytest.raises(ValidationError):
        TableBlock(
            id="t-err",
            num_rows=1,
            num_cols=1,
            cells=[TableCell(cell_id="c-err", row_index=5, col_index=0, text="Out of bounds")],
            bbox=BoundingBox(left=0, top=0, right=1, bottom=1),
        )

    # Invalid row_span < 1
    with pytest.raises(ValidationError):
        TableCell(cell_id="c-span", row_index=0, col_index=0, row_span=0)


def test_figures_without_image_libraries():
    """Test FigureBlock and ImageRef without external PIL/OpenCV requirements."""
    img_ref = ImageRef(
        uri="https://example.com/figure1.png",
        mime_type="image/png",
        width_px=1920,
        height_px=1080,
        size_bytes=245120,
    )
    fig = FigureBlock(
        id="fig-1",
        caption="Architecture Diagram",
        alt_text="Diagram showing system components",
        image_ref=img_ref,
        bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.5),
    )
    assert fig.image_ref.mime_type == "image/png"
    assert fig.image_ref.width_px == 1920
    assert fig.caption == "Architecture Diagram"


def test_formulas():
    """Test FormulaBlock expressions and inline/block flags."""
    f1 = FormulaBlock(
        id="f-1",
        expression="E = mc^2",
        format=FormulaFormat.LATEX,
        is_inline=True,
        bbox=BoundingBox(left=0.1, top=0.1, right=0.3, bottom=0.15),
    )
    assert f1.expression == "E = mc^2"
    assert f1.format == FormulaFormat.LATEX
    assert f1.is_inline is True


def test_json_serialization_and_deserialization():
    """Test full JSON serialization (model_dump_json) and deserialization (model_validate_json)."""
    meta = DocumentMetadata(id="doc-json", name="test.pdf", page_count=1)
    p0 = Page(
        page_index=0,
        width=500.0,
        height=700.0,
        blocks=[
            HeadingBlock(id="h1", text="Main Title", level=1, bbox=BoundingBox(left=0, top=0, right=1, bottom=0.1)),
            TextBlock(id="t1", text="Paragraph text line.", bbox=BoundingBox(left=0, top=0.1, right=1, bottom=0.3)),
            FormulaBlock(id="f1", expression="\\int_0^1 x dx", format=FormulaFormat.LATEX, bbox=BoundingBox(left=0, top=0.3, right=0.5, bottom=0.4)),
        ],
    )
    doc_orig = DocumentIR(
        metadata=meta,
        pages=[p0],
        reading_order=ReadingOrder(sequence=["h1", "t1", "f1"]),
    )

    json_str = doc_orig.model_dump_json(indent=2)
    assert isinstance(json_str, str)
    assert "Main Title" in json_str

    # Validate roundtrip deserialization
    doc_reconstructed = DocumentIR.model_validate_json(json_str)
    assert doc_reconstructed.metadata.id == doc_orig.metadata.id
    assert len(doc_reconstructed.pages[0].blocks) == 3
    assert doc_reconstructed.pages[0].blocks[2].block_type == BlockType.FORMULA
    assert doc_reconstructed.pages[0].blocks[2].expression == "\\int_0^1 x dx"
    assert doc_reconstructed.reading_order.sequence == ["h1", "t1", "f1"]


def test_validation_failures():
    """Test cross-page validation failures (e.g. duplicate Block IDs)."""
    meta = DocumentMetadata(id="doc-dup", name="dup.pdf", page_count=2)
    p0 = Page(
        page_index=0,
        width=100.0,
        height=100.0,
        blocks=[TextBlock(id="duplicate-id", text="P0", bbox=BoundingBox(left=0, top=0, right=1, bottom=0.1))],
    )
    p1 = Page(
        page_index=1,
        width=100.0,
        height=100.0,
        blocks=[TextBlock(id="duplicate-id", text="P1", bbox=BoundingBox(left=0, top=0, right=1, bottom=0.1))],
    )

    with pytest.raises(ValidationError) as exc_info:
        DocumentIR(metadata=meta, pages=[p0, p1])
    assert "Duplicate Block ID 'duplicate-id'" in str(exc_info.value)
