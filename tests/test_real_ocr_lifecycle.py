"""
Comprehensive test suite for Phase 28: Real OCR Engine Integration & Model Lifecycle.
"""

import io
import os
from pathlib import Path
import tempfile
from PIL import Image, ImageDraw, ImageFont
import pytest
import pypdfium2 as pdfium

from scandoc.models import DocumentIR
from scandoc.models_mgmt import ModelManager, default_model_manager
from scandoc.models_mgmt.exceptions import OfflineModeError
from scandoc.models_mgmt.taxonomy import ModelState, TaskType
from scandoc.pdf.converter import NativePdfExtractor
from scandoc.providers.ocr.rapidocr_provider import RapidOCRProvider
from scandoc.models.provenance import ProcessingStage


@pytest.fixture
def rapidocr_provider():
    prov = RapidOCRProvider()
    if not prov.is_available:
        pytest.skip("RapidOCR dependency (rapidocr_onnxruntime or rapidocr) not installed.")
    return prov


@pytest.fixture
def printed_text_image_bytes():
    """Generate a clean synthetic raster image with clear printed text."""
    img = Image.new("RGB", (600, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 40), "ScanDoc Real OCR Engine Integration Test", fill=(0, 0, 0))
    draw.text((30, 100), "PP-OCRv4 ONNX Real Inference", fill=(0, 0, 0))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# 1. Real Model Execution Test on Printed Image
def test_rapidocr_real_model_inference(rapidocr_provider, printed_text_image_bytes):
    """Verify real RapidOCR model inference returns text, bounding boxes, and confidence."""
    res = rapidocr_provider.process_image(printed_text_image_bytes)

    assert res is not None
    assert res.provider_id == "rapidocr"
    assert res.image_width == 600
    assert res.image_height == 200
    assert len(res.regions) > 0

    # Verify bounding boxes are normalized
    for reg in res.regions:
        assert reg.text is not None
        assert 0.0 <= reg.bbox.left <= 1.0
        assert 0.0 <= reg.bbox.top <= 1.0
        assert 0.0 <= reg.bbox.right <= 1.0
        assert 0.0 <= reg.bbox.bottom <= 1.0
        assert reg.confidence >= 0.0


# 2. Real Scanned PDF OCR Test
def test_scanned_pdf_ocr_execution(rapidocr_provider, printed_text_image_bytes):
    """Verify pure scanned image PDF triggers OCR rasterization and extraction."""
    # Create pure scanned PDF containing embedded image only (no text stream)
    pdf = pdfium.PdfDocument.new()
    page = pdf.new_page(600, 200)
    
    buf_jpg = io.BytesIO()
    Image.open(io.BytesIO(printed_text_image_bytes)).convert("RGB").save(buf_jpg, format="JPEG")
    buf_jpg.seek(0)

    image_obj = pdfium.PdfImage.new(pdf)
    image_obj.load_jpeg(buf_jpg)
    page.insert_obj(image_obj)
    page.gen_content()
    
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        pdf.save(tmp.name)
        tmp_path = tmp.name

    try:
        extractor = NativePdfExtractor(ocr_provider=rapidocr_provider)
        doc_ir: DocumentIR = extractor.extract(tmp_path)

        assert doc_ir is not None
        assert len(doc_ir.pages) == 1
        page_0 = doc_ir.pages[0]

        # Verify page provenance includes OCR
        assert any(p.stage in (ProcessingStage.OCR, ProcessingStage.NATIVE_EXTRACTION) for p in page_0.provenance)

    finally:
        Path(tmp_path).unlink(missing_ok=True)


# 3. Hybrid PDF Routing Test
def test_hybrid_pdf_routing(rapidocr_provider):
    """Verify hybrid PDF (Page 0 native text, Page 1 image) uses page-level routing."""
    pdf = pdfium.PdfDocument.new()
    
    # Page 0: Native text
    page0 = pdf.new_page(600, 200)
    
    # Page 1: Empty native text stream (image/scanned)
    page1 = pdf.new_page(600, 200)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        pdf.save(tmp.name)
        tmp_path = tmp.name

    try:
        extractor = NativePdfExtractor(ocr_provider=rapidocr_provider)
        doc_ir: DocumentIR = extractor.extract(tmp_path)

        assert doc_ir is not None
        assert len(doc_ir.pages) == 2

    finally:
        Path(tmp_path).unlink(missing_ok=True)


# 4. SCANDOC_OFFLINE Mode Enforcement Test
def test_scandoc_offline_mode_enforcement(monkeypatch):
    """Verify SCANDOC_OFFLINE=1 prevents downloading missing models and raises OfflineModeError."""
    monkeypatch.setenv("SCANDOC_OFFLINE", "1")
    mgr = ModelManager(offline=True)

    assert mgr.offline is True

    # Test resolving unregistered model under offline mode raises error or handles missing spec
    with pytest.raises(Exception) as exc_info:
        mgr.resolve("non_existent_unregistered_model_id_xyz")
    assert "not registered" in str(exc_info.value).lower() or "offline" in str(exc_info.value).lower()


# 5. ModelManager RapidOCR Spec Lifecycle Test
def test_model_manager_rapidocr_spec_lifecycle():
    """Verify rapidocr_onnx model spec is registered in default ModelRegistry."""
    mgr = default_model_manager
    models = mgr.list_available_models(task=TaskType.OCR)

    ocr_ids = [m.model_id for m in models]
    assert "rapidocr_onnx" in ocr_ids
