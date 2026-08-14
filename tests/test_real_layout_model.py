"""
Comprehensive test suite for Phase 29: Real Layout Detection & Deep-Learning Model Integration.
"""

import io
from pathlib import Path
import tempfile
from PIL import Image, ImageDraw
import pytest

from scandoc.models import DocumentIR
from scandoc.models_mgmt import default_model_manager
from scandoc.models_mgmt.taxonomy import TaskType
from scandoc.pdf.converter import NativePdfExtractor
from scandoc.providers.layout import (
    DocLayNetMapper,
    LayoutCategory,
    LayoutConfig,
    LayoutResult,
    RtDetrLayoutProvider,
    layout_result_to_document_ir,
)
from scandoc.providers.ocr.rapidocr_provider import RapidOCRProvider
from scandoc.models.provenance import ProcessingStage


@pytest.fixture
def rtdetr_provider():
    prov = RtDetrLayoutProvider()
    if not prov.is_available:
        pytest.skip("onnxruntime dependency not installed.")
    return prov


@pytest.fixture
def document_page_image_bytes():
    """Generate a clean synthetic document image with title, paragraph, table, and figure regions."""
    img = Image.new("RGB", (800, 1000), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Title region
    draw.rectangle([80, 50, 720, 120], fill=(230, 230, 250), outline=(0, 0, 0))
    draw.text((100, 70), "Phase 29 Deep Learning Layout Detection", fill=(0, 0, 0))

    # Paragraph region
    draw.rectangle([80, 150, 720, 450], fill=(245, 245, 245), outline=(0, 0, 0))
    draw.text((100, 170), "This is main body paragraph content evaluated by RT-DETR DocLayNet model.", fill=(0, 0, 0))

    # Table region
    draw.rectangle([80, 480, 720, 700], fill=(240, 255, 240), outline=(0, 0, 0))
    draw.text((100, 500), "Table Region Header | Column 1 | Column 2", fill=(0, 0, 0))

    # Figure region
    draw.rectangle([80, 730, 720, 920], fill=(255, 240, 245), outline=(0, 0, 0))
    draw.text((100, 750), "Figure Graphic Diagram Area", fill=(0, 0, 0))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# 1. RT-DETR Provider Capability & Availability Test
def test_rtdetr_layout_provider_initialization(rtdetr_provider):
    """Verify RT-DETR Layout Provider initialization and supported categories."""
    assert rtdetr_provider.provider_id == "rt_detr_layout"
    assert "RT-DETR" in rtdetr_provider.model_id
    assert LayoutCategory.TITLE in rtdetr_provider.supported_categories
    assert LayoutCategory.TABLE in rtdetr_provider.supported_categories
    assert LayoutCategory.FIGURE in rtdetr_provider.supported_categories


# 2. Real Image Layout Detection Test
def test_rtdetr_layout_detection_on_image(rtdetr_provider, document_page_image_bytes):
    """Verify layout detection on document page image returns normalized regions."""
    result: LayoutResult = rtdetr_provider.detect_layout(document_page_image_bytes, page_index=0)

    assert result is not None
    assert result.provider_id == "rt_detr_layout"
    assert result.image_width == 800
    assert result.image_height == 1000
    assert len(result.regions) >= 2

    for reg in result.regions:
        assert reg.category in rtdetr_provider.supported_categories
        assert 0.0 <= reg.bbox.left <= 1.0
        assert 0.0 <= reg.bbox.top <= 1.0
        assert 0.0 <= reg.bbox.right <= 1.0
        assert 0.0 <= reg.bbox.bottom <= 1.0
        assert reg.confidence >= 0.0


# 3. Layout Result to DocumentIR Conversion Test
def test_layout_converter_to_document_ir(rtdetr_provider, document_page_image_bytes):
    """Verify LayoutResult is correctly mapped into DocumentIR typed blocks."""
    result = rtdetr_provider.detect_layout(document_page_image_bytes, page_index=0)
    doc_ir: DocumentIR = layout_result_to_document_ir(result)

    assert doc_ir is not None
    assert len(doc_ir.pages) == 1
    page_0 = doc_ir.pages[0]
    assert len(page_0.blocks) == len(result.regions)

    for block in page_0.blocks:
        assert block.provenance is not None
        assert block.provenance.provider == "rt_detr_layout"
        assert block.provenance.stage == ProcessingStage.LAYOUT_ANALYSIS


# 4. DocLayNet Taxonomy Class Mapper Test
def test_doclaynet_taxonomy_mapper():
    """Verify DocLayNet 11-class index mapping to scanDOC LayoutCategory taxonomy."""
    assert DocLayNetMapper.map_class(7) == LayoutCategory.TITLE
    assert DocLayNetMapper.map_class(8) == LayoutCategory.TABLE
    assert DocLayNetMapper.map_class(6) == LayoutCategory.FIGURE
    assert DocLayNetMapper.map_class(9) == LayoutCategory.PARAGRAPH
    assert DocLayNetMapper.map_class("section_header") == LayoutCategory.TITLE


# 5. ModelManager Spec Lifecycle Test for rtdetr_doclaynet
def test_model_manager_rtdetr_spec_lifecycle():
    """Verify rtdetr_doclaynet is registered in ModelRegistry for TaskType.LAYOUT."""
    mgr = default_model_manager
    models = mgr.list_available_models(task=TaskType.LAYOUT)

    layout_ids = [m.model_id for m in models]
    assert "rtdetr_doclaynet" in layout_ids
