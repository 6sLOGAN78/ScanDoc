"""
Phase 1B: Document IR boundary validation test suite.

Verifies:
1. All 7 realistic document fixtures represent full layout, text, tables, figures, formulas,
   provenance, and reading order without data loss.
2. JSON roundtrip serialization (DocumentIR -> JSON -> DocumentIR) maintains 100% semantic equivalence.
3. Strict zero-dependency isolation (no imports of PyTorch, ONNX, OpenCV, OCR libraries, or Transformers).
"""

import sys
import pytest
from scandoc.core import DocumentIR

from fixtures.realistic_documents import (
    create_simple_digital_pdf,
    create_scanned_ocr_doc,
    create_two_column_paper,
    create_table_merged_cells,
    create_figure_and_caption,
    create_formula_doc,
    create_multipage_headers_footers,
)


@pytest.fixture
def all_document_fixtures():
    """Returns dictionary of all 7 realistic document fixtures."""
    return {
        "simple_digital_pdf": create_simple_digital_pdf(),
        "scanned_ocr_doc": create_scanned_ocr_doc(),
        "two_column_paper": create_two_column_paper(),
        "table_merged_cells": create_table_merged_cells(),
        "figure_and_caption": create_figure_and_caption(),
        "formula_doc": create_formula_doc(),
        "multipage_headers_footers": create_multipage_headers_footers(),
    }


def test_fixture_1_simple_digital_pdf():
    """Verify simple digital PDF representation."""
    doc = create_simple_digital_pdf()
    assert doc.metadata.name == "annual_report_2025.pdf"
    assert len(doc.pages) == 1
    assert len(doc.pages[0].blocks) == 3
    assert doc.pages[0].blocks[0].text == "Annual Financial Report 2025"
    assert doc.pages[0].blocks[0].provenance.provider == "pypdfium2"
    assert doc.reading_order.sequence == ["b-h1", "b-h2", "b-p1"]


def test_fixture_2_scanned_ocr_doc():
    """Verify scanned document with OCR polygon and word spans."""
    doc = create_scanned_ocr_doc()
    assert doc.pages[0].dpi == 300
    blk = doc.pages[0].blocks[0]
    assert blk.provenance.model == "PP-OCRv4"
    assert blk.provenance.confidence == 0.94
    assert len(blk.polygon) == 4
    assert len(blk.spans) == 2
    assert blk.spans[0].confidence == 0.99


def test_fixture_3_two_column_paper():
    """Verify two-column paper reading order and spatial bounds."""
    doc = create_two_column_paper()
    assert len(doc.pages[0].blocks) == 5
    seq = doc.reading_order.sequence
    # Title -> Col 1 H -> Col 1 P -> Col 2 H -> Col 2 P
    assert seq == ["b-title", "b-col1-h", "b-col1-p", "b-col2-h", "b-col2-p"]
    # Check column bounding box separation
    b_col1 = doc.get_block("b-col1-p").bbox
    b_col2 = doc.get_block("b-col2-p").bbox
    assert b_col1.right <= 0.50
    assert b_col2.left >= 0.50


def test_fixture_4_table_merged_cells():
    """Verify table structure, merged cell spans, and captions."""
    doc = create_table_merged_cells()
    table = doc.pages[0].blocks[0]
    assert table.num_rows == 3
    assert table.num_cols == 2
    assert table.cells[0].col_span == 2  # Merged header
    assert table.cells[1].row_span == 2  # Merged row cell
    assert table.caption == "Table 1: Regional Growth Performance"


def test_fixture_5_figure_and_caption():
    """Verify figure asset reference, alt text, and caption block targeting."""
    doc = create_figure_and_caption()
    fig = doc.pages[0].blocks[0]
    cap = doc.pages[0].blocks[1]
    assert fig.image_ref.mime_type == "image/png"
    assert fig.image_ref.width_px == 1600
    assert cap.target_block_id == fig.id


def test_fixture_6_formula_doc():
    """Verify block and inline LaTeX mathematical formulas."""
    doc = create_formula_doc()
    f_block = doc.get_block("b-f-block")
    f_inline = doc.get_block("b-f-inline")
    assert f_block.is_inline is False
    assert f_block.format.value == "LATEX"
    assert f_inline.is_inline is True


def test_fixture_7_multipage_headers_footers():
    """Verify multi-page document structure and body/furniture separation."""
    doc = create_multipage_headers_footers()
    assert len(doc.pages) == 3
    assert len(doc.structure.furniture_block_ids) == 6  # 3 headers + 3 footers
    assert len(doc.structure.body_block_ids) == 3       # 3 body paragraphs
    # Verify reading order includes body blocks and excludes furniture
    for b_id in doc.structure.body_block_ids:
        assert b_id in doc.reading_order.sequence
    for f_id in doc.structure.furniture_block_ids:
        assert f_id not in doc.reading_order.sequence


def test_json_roundtrip_semantic_equivalence(all_document_fixtures):
    """
    Test DocumentIR -> JSON -> DocumentIR roundtrip across all 7 realistic document fixtures
    to guarantee 100% semantic equivalence.
    """
    for name, doc_orig in all_document_fixtures.items():
        json_str1 = doc_orig.model_dump_json(indent=2)
        doc_reconstructed = DocumentIR.model_validate_json(json_str1)
        json_str2 = doc_reconstructed.model_dump_json(indent=2)
        
        # Verify strict JSON equality after roundtrip
        assert json_str1 == json_str2, f"Roundtrip failed for fixture '{name}'"
        assert doc_orig == doc_reconstructed, f"Semantic object equality failed for '{name}'"


def test_strict_dependency_isolation():
    """
    Verify that importing scandoc.core or scandoc.models does NOT import or depend on
    heavy ML runtime frameworks or OCR libraries.
    """
    forbidden_modules = [
        "torch",
        "onnxruntime",
        "cv2",
        "rapidocr",
        "rapidocr_onnxruntime",
        "pytesseract",
        "easyocr",
        "paddleocr",
        "transformers",
        "pycuda",
    ]
    
    loaded_modules = set(sys.modules.keys())
    for forbidden in forbidden_modules:
        matching = [mod for mod in loaded_modules if mod == forbidden or mod.startswith(forbidden + ".")]
        assert len(matching) == 0, f"Core IR unexpectedly imported forbidden module: {matching}"
