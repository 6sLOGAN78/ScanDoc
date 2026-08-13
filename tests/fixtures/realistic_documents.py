"""
Realistic document fixtures for testing DocumentIR boundary validation in Phase 1B.
"""

from scandoc.core import (
    DocumentIR,
    DocumentMetadata,
    DocumentStructure,
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


def create_simple_digital_pdf() -> DocumentIR:
    """Fixture 1: Simple digital PDF with native text extraction."""
    meta = DocumentMetadata(
        id="doc-digital-001",
        name="annual_report_2025.pdf",
        mime_type="application/pdf",
        page_count=1,
        created_at="2026-08-14T00:00:00Z",
    )
    prov = Provenance(
        provider="pypdfium2",
        stage=ProcessingStage.NATIVE_EXTRACTION,
        version="4.2.0",
        confidence=1.0,
    )
    
    h1 = HeadingBlock(
        id="b-h1",
        text="Annual Financial Report 2025",
        level=1,
        bbox=BoundingBox(left=0.1, top=0.05, right=0.9, bottom=0.10, page_index=0),
        reading_order_index=0,
        provenance=prov,
    )
    h2 = HeadingBlock(
        id="b-h2",
        text="1. Executive Summary",
        level=2,
        bbox=BoundingBox(left=0.1, top=0.12, right=0.9, bottom=0.16, page_index=0),
        reading_order_index=1,
        provenance=prov,
    )
    p1 = ParagraphBlock(
        id="b-p1",
        text="Total revenue for the fiscal year 2025 reached $4.2 billion, representing a 15% year-over-year growth.",
        bbox=BoundingBox(left=0.1, top=0.18, right=0.9, bottom=0.28, page_index=0),
        reading_order_index=2,
        provenance=prov,
    )

    page0 = Page(
        page_index=0,
        width=612.0,
        height=792.0,
        unit=SizeUnit.POINTS,
        blocks=[h1, h2, p1],
        provenance=[prov],
    )
    
    return DocumentIR(
        metadata=meta,
        pages=[page0],
        reading_order=ReadingOrder(sequence=["b-h1", "b-h2", "b-p1"]),
        structure=DocumentStructure(
            heading_tree={"b-h1": ["b-h2"], "b-h2": ["b-p1"]},
            body_block_ids=["b-h1", "b-h2", "b-p1"],
            furniture_block_ids=[],
        ),
    )


def create_scanned_ocr_doc() -> DocumentIR:
    """Fixture 2: Scanned document with OCR text, polygons, and confidence scores."""
    meta = DocumentMetadata(
        id="doc-scanned-002",
        name="scanned_invoice_scan.pdf",
        mime_type="application/pdf",
        page_count=1,
    )
    prov = Provenance(
        provider="rapidocr",
        model="PP-OCRv4",
        stage=ProcessingStage.OCR,
        confidence=0.94,
    )
    
    poly1 = [
        Point2D(x=0.08, y=0.04),
        Point2D(x=0.88, y=0.04),
        Point2D(x=0.88, y=0.11),
        Point2D(x=0.08, y=0.11),
    ]
    
    span1 = TextSpan(text="INVOICE", start_char_idx=0, end_char_idx=7, confidence=0.99)
    span2 = TextSpan(text="#98421", start_char_idx=8, end_char_idx=14, confidence=0.92)
    
    txt1 = TextBlock(
        id="b-ocr-1",
        text="INVOICE #98421",
        bbox=BoundingBox(left=0.08, top=0.04, right=0.88, bottom=0.11, page_index=0),
        polygon=poly1,
        spans=[span1, span2],
        reading_order_index=0,
        provenance=prov,
    )
    
    page0 = Page(
        page_index=0,
        width=2480.0,
        height=3508.0,
        dpi=300,
        unit=SizeUnit.PIXELS,
        blocks=[txt1],
        provenance=[prov],
    )
    
    return DocumentIR(
        metadata=meta,
        pages=[page0],
        reading_order=ReadingOrder(sequence=["b-ocr-1"]),
        structure=DocumentStructure(body_block_ids=["b-ocr-1"]),
    )


def create_two_column_paper() -> DocumentIR:
    """Fixture 3: Two-column academic paper layout with non-linear reading order."""
    meta = DocumentMetadata(
        id="doc-paper-003",
        name="attention_paper.pdf",
        page_count=1,
    )
    prov = Provenance(provider="rt-detr", stage=ProcessingStage.LAYOUT_ANALYSIS)
    
    # Title across page width
    title = HeadingBlock(
        id="b-title",
        text="Attention Is All You Need in Document Processing",
        level=1,
        bbox=BoundingBox(left=0.1, top=0.05, right=0.9, bottom=0.12, page_index=0),
        reading_order_index=0,
        provenance=prov,
    )
    
    # Column 1 elements (left: 0.1 to 0.48)
    col1_h = HeadingBlock(
        id="b-col1-h",
        text="1. Introduction",
        level=2,
        bbox=BoundingBox(left=0.1, top=0.15, right=0.48, bottom=0.19, page_index=0),
        reading_order_index=1,
        provenance=prov,
    )
    col1_p = ParagraphBlock(
        id="b-col1-p",
        text="Document layout analysis has evolved significantly with deep learning techniques.",
        bbox=BoundingBox(left=0.1, top=0.20, right=0.48, bottom=0.85, page_index=0),
        reading_order_index=2,
        provenance=prov,
    )
    
    # Column 2 elements (left: 0.52 to 0.90)
    col2_h = HeadingBlock(
        id="b-col2-h",
        text="2. Related Work",
        level=2,
        bbox=BoundingBox(left=0.52, top=0.15, right=0.90, bottom=0.19, page_index=0),
        reading_order_index=3,
        provenance=prov,
    )
    col2_p = ParagraphBlock(
        id="b-col2-p",
        text="Early rule-based layout heuristics focused primarily on whitespace histogram analysis.",
        bbox=BoundingBox(left=0.52, top=0.20, right=0.90, bottom=0.85, page_index=0),
        reading_order_index=4,
        provenance=prov,
    )
    
    page0 = Page(
        page_index=0,
        width=612.0,
        height=792.0,
        blocks=[title, col1_h, col1_p, col2_h, col2_p],
    )
    
    # Explicit reading order: Title -> Col1 Heading -> Col1 Para -> Col2 Heading -> Col2 Para
    return DocumentIR(
        metadata=meta,
        pages=[page0],
        reading_order=ReadingOrder(
            sequence=["b-title", "b-col1-h", "b-col1-p", "b-col2-h", "b-col2-p"]
        ),
        structure=DocumentStructure(
            heading_tree={
                "b-title": ["b-col1-h", "b-col2-h"],
                "b-col1-h": ["b-col1-p"],
                "b-col2-h": ["b-col2-p"],
            },
            body_block_ids=["b-title", "b-col1-h", "b-col1-p", "b-col2-h", "b-col2-p"],
        ),
    )


def create_table_merged_cells() -> DocumentIR:
    """Fixture 4: Document with complex table featuring merged column and row spans."""
    meta = DocumentMetadata(
        id="doc-table-004",
        name="financial_table.pdf",
        page_count=1,
    )
    prov = Provenance(provider="slanet", stage=ProcessingStage.TABLE_RECOGNITION, confidence=0.92)
    
    # Row 0: Merged Header (Spans Col 0 and Col 1)
    cell_h0 = TableCell(
        cell_id="cell-0-0",
        row_index=0,
        col_index=0,
        row_span=1,
        col_span=2,
        is_header=True,
        text="Q4 Financial Metrics",
        bbox=BoundingBox(left=0.1, top=0.2, right=0.9, bottom=0.3, page_index=0),
    )
    
    # Row 1 & 2: Row 1 Col 0 spans 2 rows
    cell_r1_c0 = TableCell(
        cell_id="cell-1-0",
        row_index=1,
        col_index=0,
        row_span=2,
        col_span=1,
        is_header=False,
        text="North America Region",
        bbox=BoundingBox(left=0.1, top=0.3, right=0.5, bottom=0.5, page_index=0),
    )
    cell_r1_c1 = TableCell(
        cell_id="cell-1-1",
        row_index=1,
        col_index=1,
        row_span=1,
        col_span=1,
        is_header=False,
        text="$1,200,000",
        bbox=BoundingBox(left=0.5, top=0.3, right=0.9, bottom=0.4, page_index=0),
    )
    cell_r2_c1 = TableCell(
        cell_id="cell-2-1",
        row_index=2,
        col_index=1,
        row_span=1,
        col_span=1,
        is_header=False,
        text="$1,450,000",
        bbox=BoundingBox(left=0.5, top=0.4, right=0.9, bottom=0.5, page_index=0),
    )
    
    table_block = TableBlock(
        id="b-table-1",
        num_rows=3,
        num_cols=2,
        cells=[cell_h0, cell_r1_c0, cell_r1_c1, cell_r2_c1],
        caption="Table 1: Regional Growth Performance",
        bbox=BoundingBox(left=0.1, top=0.18, right=0.9, bottom=0.52, page_index=0),
        reading_order_index=0,
        provenance=prov,
    )
    
    page0 = Page(page_index=0, width=612.0, height=792.0, blocks=[table_block])
    return DocumentIR(
        metadata=meta,
        pages=[page0],
        reading_order=ReadingOrder(sequence=["b-table-1"]),
        structure=DocumentStructure(body_block_ids=["b-table-1"]),
    )


def create_figure_and_caption() -> DocumentIR:
    """Fixture 5: Document with image figure, caption, and asset reference."""
    meta = DocumentMetadata(
        id="doc-fig-005",
        name="architecture_paper.pdf",
        page_count=1,
    )
    prov = Provenance(provider="rt-detr", stage=ProcessingStage.LAYOUT_ANALYSIS)
    
    img_ref = ImageRef(
        uri="file:///workspace/assets/arch_diagram.png",
        path="/workspace/assets/arch_diagram.png",
        mime_type="image/png",
        width_px=1600,
        height_px=900,
        size_bytes=420100,
    )
    
    fig = FigureBlock(
        id="b-fig-1",
        caption="System Component Topology",
        alt_text="Diagram illustrating data flow between PDF inspector and ONNX models.",
        image_ref=img_ref,
        bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.5, page_index=0),
        reading_order_index=0,
        provenance=prov,
    )
    
    caption = CaptionBlock(
        id="b-cap-1",
        text="Figure 1: High-level System Component Topology.",
        target_block_id="b-fig-1",
        bbox=BoundingBox(left=0.1, top=0.51, right=0.9, bottom=0.55, page_index=0),
        reading_order_index=1,
        provenance=prov,
    )
    
    page0 = Page(page_index=0, width=612.0, height=792.0, blocks=[fig, caption])
    return DocumentIR(
        metadata=meta,
        pages=[page0],
        reading_order=ReadingOrder(sequence=["b-fig-1", "b-cap-1"]),
        structure=DocumentStructure(body_block_ids=["b-fig-1", "b-cap-1"]),
    )


def create_formula_doc() -> DocumentIR:
    """Fixture 6: Document with block and inline mathematical formulas."""
    meta = DocumentMetadata(
        id="doc-formula-006",
        name="math_notes.pdf",
        page_count=1,
    )
    prov = Provenance(provider="nougat", stage=ProcessingStage.FORMULA_RECOGNITION, confidence=0.98)
    
    p1 = ParagraphBlock(
        id="b-p1",
        text="The Gaussian integral is a fundamental constant in probability theory.",
        bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.15, page_index=0),
        reading_order_index=0,
    )
    
    # Block math formula
    f_block = FormulaBlock(
        id="b-f-block",
        expression=r"\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}",
        format=FormulaFormat.LATEX,
        is_inline=False,
        bbox=BoundingBox(left=0.15, top=0.18, right=0.85, bottom=0.28, page_index=0),
        reading_order_index=1,
        provenance=prov,
    )
    
    # Inline math formula
    f_inline = FormulaBlock(
        id="b-f-inline",
        expression=r"e^{i\pi} + 1 = 0",
        format=FormulaFormat.LATEX,
        is_inline=True,
        bbox=BoundingBox(left=0.1, top=0.32, right=0.4, bottom=0.36, page_index=0),
        reading_order_index=2,
        provenance=prov,
    )
    
    page0 = Page(page_index=0, width=612.0, height=792.0, blocks=[p1, f_block, f_inline])
    return DocumentIR(
        metadata=meta,
        pages=[page0],
        reading_order=ReadingOrder(sequence=["b-p1", "b-f-block", "b-f-inline"]),
        structure=DocumentStructure(body_block_ids=["b-p1", "b-f-block", "b-f-inline"]),
    )


def create_multipage_headers_footers() -> DocumentIR:
    """Fixture 7: 3-Page document with headers and footers (furniture separation)."""
    meta = DocumentMetadata(
        id="doc-multi-007",
        name="quarterly_report.pdf",
        page_count=3,
    )
    prov = Provenance(provider="pypdfium2", stage=ProcessingStage.NATIVE_EXTRACTION)
    
    pages = []
    body_ids = []
    furniture_ids = []
    reading_seq = []
    
    for i in range(3):
        header_id = f"b-hdr-p{i}"
        footer_id = f"b-ftr-p{i}"
        body_id = f"b-body-p{i}"
        
        hdr = TextBlock(
            id=header_id,
            text=f"CONFIDENTIAL REPORT - PAGE {i + 1}",
            bbox=BoundingBox(left=0.1, top=0.02, right=0.9, bottom=0.05, page_index=i),
            provenance=prov,
        )
        body = ParagraphBlock(
            id=body_id,
            text=f"Content paragraph for page {i + 1}.",
            bbox=BoundingBox(left=0.1, top=0.10, right=0.9, bottom=0.90, page_index=i),
            provenance=prov,
        )
        ftr = TextBlock(
            id=footer_id,
            text=f"Page {i + 1} of 3",
            bbox=BoundingBox(left=0.4, top=0.94, right=0.6, bottom=0.98, page_index=i),
            provenance=prov,
        )
        
        furniture_ids.extend([header_id, footer_id])
        body_ids.append(body_id)
        reading_seq.append(body_id)  # Reading order includes body, excludes furniture
        
        p = Page(
            page_index=i,
            width=612.0,
            height=792.0,
            blocks=[hdr, body, ftr],
        )
        pages.append(p)
        
    return DocumentIR(
        metadata=meta,
        pages=pages,
        reading_order=ReadingOrder(sequence=reading_seq),
        structure=DocumentStructure(
            body_block_ids=body_ids,
            furniture_block_ids=furniture_ids,
        ),
    )
