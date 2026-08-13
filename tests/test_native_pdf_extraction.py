"""
Unit and integration test suite for Native PDF Extraction (Phase 3).
"""

import time
import pytest
import fitz  # PyMuPDF for generating test PDF fixtures

from scandoc.models import BlockType, DocumentIR, ProcessingStage
from scandoc.pdf import (
    NativePdfExtractor,
    MalformedPdfError,
    EmptyPdfError,
)
from fixtures.pdf_fixtures import (
    generate_digital_pdf_bytes,
    generate_image_pdf_bytes,
    generate_hybrid_pdf_bytes,
)


def test_extract_simple_digital_pdf():
    """Test extracting native text, spans, page number, and bounding boxes from a digital PDF."""
    pdf_bytes = generate_digital_pdf_bytes(page_count=1, text="Native PDF Extraction Line")
    extractor = NativePdfExtractor()
    doc: DocumentIR = extractor.extract(pdf_bytes, file_path="sample_digital.pdf")

    assert doc.metadata.name == "sample_digital.pdf"
    assert len(doc.pages) == 1
    assert len(doc.pages[0].blocks) >= 1
    
    blk = doc.pages[0].blocks[0]
    assert blk.block_type == BlockType.TEXT
    assert "Native PDF Extraction Line" in blk.text
    assert blk.provenance.provider == "pypdfium2"
    assert blk.provenance.stage == ProcessingStage.NATIVE_EXTRACTION
    assert blk.bbox.is_normalized is True
    assert 0.0 <= blk.bbox.left <= blk.bbox.right <= 1.0
    assert 0.0 <= blk.bbox.top <= blk.bbox.bottom <= 1.0


def test_extract_multipage_pdf():
    """Test extracting a 3-page digital PDF."""
    pdf_bytes = generate_digital_pdf_bytes(page_count=3, text="Multi Page PDF Test")
    extractor = NativePdfExtractor()
    doc = extractor.extract(pdf_bytes)

    assert len(doc.pages) == 3
    assert doc.metadata.page_count == 3
    for i in range(3):
        assert doc.pages[i].page_index == i
        assert len(doc.pages[i].blocks) >= 1
        assert doc.pages[i].blocks[0].bbox.page_index == i


def test_extract_text_different_fonts():
    """Test extracting text blocks with varying font sizes and styles."""
    doc_pdf = fitz.open()
    page = doc_pdf.new_page(width=612, height=792)
    page.insert_text((50, 100), "Title in Large Helvetica 24pt", fontsize=24)
    page.insert_text((50, 200), "Subtitle in Times Roman 14pt", fontsize=14)
    page.insert_text((50, 300), "Regular Body Courier 10pt", fontsize=10)
    pdf_bytes = doc_pdf.tobytes()
    doc_pdf.close()

    extractor = NativePdfExtractor()
    doc = extractor.extract(pdf_bytes)

    assert len(doc.pages[0].blocks) == 3
    assert "Title in Large" in doc.pages[0].blocks[0].text
    assert "Subtitle in Times" in doc.pages[0].blocks[1].text
    assert "Regular Body" in doc.pages[0].blocks[2].text


def test_extract_pdf_with_images():
    """Test detecting native embedded image figures and preserving asset metadata."""
    pdf_bytes = generate_hybrid_pdf_bytes()
    extractor = NativePdfExtractor()
    doc = extractor.extract(pdf_bytes)

    page = doc.pages[0]
    fig_blocks = [b for b in page.blocks if b.block_type == BlockType.FIGURE]
    assert len(fig_blocks) == 1
    
    fig = fig_blocks[0]
    assert fig.image_ref is not None
    assert fig.image_ref.mime_type == "image/png"
    assert fig.image_ref.width_px > 0
    assert fig.image_ref.height_px > 0
    assert fig.provenance.stage == ProcessingStage.NATIVE_EXTRACTION


def test_extract_rotated_page():
    """Test extracting text from a rotated PDF page (90 degrees)."""
    doc_pdf = fitz.open()
    page = doc_pdf.new_page(width=612, height=792)
    page.insert_text((100, 100), "Rotated Page Content", fontsize=16)
    page.set_rotation(90)
    pdf_bytes = doc_pdf.tobytes()
    doc_pdf.close()

    extractor = NativePdfExtractor()
    doc = extractor.extract(pdf_bytes)

    assert doc.pages[0].rotation == 90
    assert len(doc.pages[0].blocks) >= 1
    bbox = doc.pages[0].blocks[0].bbox
    assert 0.0 <= bbox.left <= bbox.right <= 1.0
    assert 0.0 <= bbox.top <= bbox.bottom <= 1.0


def test_extract_different_page_dimensions():
    """Test extracting landscape vs portrait page dimensions."""
    doc_pdf = fitz.open()
    page_portrait = doc_pdf.new_page(width=612, height=792)
    page_portrait.insert_text((50, 50), "Portrait Page")
    page_landscape = doc_pdf.new_page(width=792, height=612)
    page_landscape.insert_text((50, 50), "Landscape Page")
    pdf_bytes = doc_pdf.tobytes()
    doc_pdf.close()

    extractor = NativePdfExtractor()
    doc = extractor.extract(pdf_bytes)

    assert doc.pages[0].width == 612.0
    assert doc.pages[0].height == 792.0
    assert doc.pages[1].width == 792.0
    assert doc.pages[1].height == 612.0


def test_extract_empty_page():
    """Test extracting a PDF page with zero text and zero images."""
    doc_pdf = fitz.open()
    doc_pdf.new_page(width=612, height=792)  # Blank page
    pdf_bytes = doc_pdf.tobytes()
    doc_pdf.close()

    extractor = NativePdfExtractor()
    doc = extractor.extract(pdf_bytes)

    assert len(doc.pages) == 1
    assert len(doc.pages[0].blocks) == 0


def test_extract_metadata():
    """Test extraction of document metadata (title, author, creation date)."""
    doc_pdf = fitz.open()
    page = doc_pdf.new_page(width=612, height=792)
    page.insert_text((100, 100), "Sample Text")
    doc_pdf.set_metadata({
        "title": "Test Title Document",
        "author": "scanDOC Test Suite",
        "subject": "Unit Testing",
    })
    pdf_bytes = doc_pdf.tobytes()
    doc_pdf.close()

    extractor = NativePdfExtractor()
    doc = extractor.extract(pdf_bytes)

    assert doc.metadata.title == "Test Title Document"
    assert doc.metadata.author == "scanDOC Test Suite"


def test_malformed_pdf_error():
    """Test malformed input raises MalformedPdfError."""
    extractor = NativePdfExtractor()
    with pytest.raises(MalformedPdfError):
        extractor.extract(b"CORRUPTED_NOT_A_PDF")


def test_empty_pdf_error():
    """Test 0-byte input raises EmptyPdfError."""
    extractor = NativePdfExtractor()
    with pytest.raises(EmptyPdfError):
        extractor.extract(b"")


def test_performance_fast_path():
    """
    Measure native PDF extraction performance.
    
    Must process a 10-page digital PDF in < 100ms total (sub-10ms per page).
    """
    pdf_bytes = generate_digital_pdf_bytes(page_count=10, text="Performance Benchmark Text Line")
    extractor = NativePdfExtractor()

    start_time = time.perf_counter()
    doc = extractor.extract(pdf_bytes)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    assert len(doc.pages) == 10
    assert elapsed_ms < 100.0, f"Native extraction took {elapsed_ms:.2f} ms, expected < 100 ms"
    print(f"\n[PERFORMANCE] Native PDF Extraction speed: {elapsed_ms:.2f} ms for 10 pages ({elapsed_ms/10:.2f} ms/page)")
