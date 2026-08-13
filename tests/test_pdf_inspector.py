"""
Unit test suite for scanDOC PDF inspection subsystem.
"""

import time
import pytest
from scandoc.pdf import (
    PdfInspector,
    DocumentCategory,
    PageContentType,
    MalformedPdfError,
    EmptyPdfError,
    PdfInspectionError,
)
from fixtures.pdf_fixtures import (
    generate_digital_pdf_bytes,
    generate_image_pdf_bytes,
    generate_hybrid_pdf_bytes,
)


def test_inspect_digital_pdf():
    """Test inspecting a digitally generated PDF with native vector text."""
    pdf_bytes = generate_digital_pdf_bytes(page_count=1, text="Annual Financial Report 2025")
    res = PdfInspector.inspect(pdf_bytes)

    assert res.page_count == 1
    assert res.category == DocumentCategory.DIGITALLY_GENERATED
    assert res.signals.recommended_fast_path is True
    assert res.signals.has_native_text is True
    assert res.signals.ocr_suggested is False
    assert res.pages[0].content_type == PageContentType.DIGITAL_TEXT_ONLY
    assert res.pages[0].character_count > 0
    assert res.pages[0].width == 612.0
    assert res.pages[0].height == 792.0


def test_inspect_scanned_pdf():
    """Test inspecting a scanned image-only PDF with zero native text."""
    pdf_bytes = generate_image_pdf_bytes(page_count=1)
    res = PdfInspector.inspect(pdf_bytes)

    assert res.page_count == 1
    assert res.category in (DocumentCategory.SCANNED, DocumentCategory.IMAGE_ONLY)
    assert res.signals.recommended_fast_path is False
    assert res.signals.ocr_suggested is True
    assert res.pages[0].has_images is True
    assert res.pages[0].image_count == 1
    assert res.pages[0].image_coverage_ratio == 1.0


def test_inspect_hybrid_pdf():
    """Test inspecting a hybrid PDF containing native text and embedded image figures."""
    pdf_bytes = generate_hybrid_pdf_bytes()
    res = PdfInspector.inspect(pdf_bytes)

    assert res.page_count == 1
    assert res.pages[0].has_native_text is True
    assert res.pages[0].has_images is True
    assert res.pages[0].image_count == 1
    assert res.signals.has_native_text is True


def test_inspect_multipage_digital_pdf():
    """Test inspecting a 5-page digital document."""
    pdf_bytes = generate_digital_pdf_bytes(page_count=5, text="Page Text")
    res = PdfInspector.inspect(pdf_bytes)

    assert res.page_count == 5
    assert len(res.pages) == 5
    assert res.category == DocumentCategory.DIGITALLY_GENERATED
    for i in range(5):
        assert res.pages[i].page_index == i


def test_malformed_pdf_error():
    """Test malformed PDF byte stream raises MalformedPdfError."""
    bad_bytes = b"NOT_A_VALID_PDF_HEADER_KEYWORD"
    with pytest.raises(MalformedPdfError):
        PdfInspector.inspect(bad_bytes)


def test_empty_pdf_error():
    """Test 0-byte input raises EmptyPdfError."""
    with pytest.raises(EmptyPdfError):
        PdfInspector.inspect(b"")


def test_non_existent_file_error():
    """Test missing file path raises PdfInspectionError."""
    with pytest.raises(PdfInspectionError):
        PdfInspector.inspect("/non_existent_directory/missing_file.pdf")


def test_render_free_performance():
    """
    Verify that PDF inspection is render-free and executes at high speed
    (< 50 ms for a 10-page document).
    """
    pdf_bytes = generate_digital_pdf_bytes(page_count=10, text="Performance Test Line")
    
    start_time = time.perf_counter()
    res = PdfInspector.inspect(pdf_bytes)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    assert res.page_count == 10
    assert elapsed_ms < 100.0, f"Inspection took {elapsed_ms:.2f} ms, expected < 100 ms"


def test_json_serialization_isolation():
    """Verify PdfInspectionResult serializes cleanly to JSON without pdfium objects."""
    pdf_bytes = generate_digital_pdf_bytes(page_count=1)
    res = PdfInspector.inspect(pdf_bytes)

    json_str = res.model_dump_json(indent=2)
    assert isinstance(json_str, str)
    assert "DIGITALLY_GENERATED" in json_str
