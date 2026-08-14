"""
Comprehensive test suite for Phase 32: Local Multimodal Vision-Language Model (VLM) & Visual Q&A Engine Integration.
"""

import io
from pathlib import Path
import tempfile
from PIL import Image, ImageDraw
import pytest

from scandoc.models import DocumentIR, DocumentMetadata, Page
from scandoc.models.geometry import BoundingBox
from scandoc.models_mgmt import default_model_manager
from scandoc.models_mgmt.taxonomy import TaskType
from scandoc.providers.vlm import (
    LocalVlmProvider,
    VlmConfig,
    VlmExecutionMode,
    VlmRequest,
    VlmResult,
    VlmTaskType,
)
from scandoc.models.provenance import ProcessingStage


@pytest.fixture
def vlm_provider():
    prov = LocalVlmProvider()
    if not prov.is_available:
        pytest.skip("VLM provider dependencies not available.")
    return prov


@pytest.fixture
def bar_chart_image_bytes():
    """Generate a clean synthetic bar chart visual image."""
    img = Image.new("RGB", (500, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Axes
    draw.line([50, 250, 450, 250], fill=(0, 0, 0), width=2)
    draw.line([50, 50, 50, 250], fill=(0, 0, 0), width=2)

    # Bars
    draw.rectangle([80, 150, 140, 250], fill=(100, 150, 250))
    draw.rectangle([180, 100, 240, 250], fill=(100, 150, 250))
    draw.rectangle([280, 70, 340, 250], fill=(100, 150, 250))
    draw.rectangle([380, 40, 440, 250], fill=(100, 150, 250))

    draw.text((150, 20), "Quarterly Sales Trajectory Chart", fill=(0, 0, 0))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# 1. Local VLM Provider Capability & Availability Test
def test_local_vlm_provider_initialization(vlm_provider):
    """Verify Local VLM Provider initialization and metadata."""
    assert vlm_provider.provider_id == "local_vlm_engine"
    assert "SmolVLM" in vlm_provider.model_id or "Qwen2-VL" in vlm_provider.model_id


# 2. Real Image Captioning Test
def test_real_image_captioning(vlm_provider, bar_chart_image_bytes):
    """Verify image captioning generates natural-language visual description."""
    req = VlmRequest(
        task=VlmTaskType.CAPTION_GENERATION,
        prompt="Generate a detailed natural language caption for this chart image.",
        image_bytes=bar_chart_image_bytes,
        output_format="text",
    )
    res: VlmResult = vlm_provider.analyze(req)

    assert res is not None
    assert res.provider_id == "local_vlm_engine"
    assert res.execution_mode == VlmExecutionMode.LOCAL
    assert res.text_result is not None
    assert len(res.text_result) > 0
    assert res.confidence >= 0.0


# 3. Real Visual Question Answering (VQA) Test
def test_real_visual_question_answering(vlm_provider, bar_chart_image_bytes):
    """Verify visual Q&A generates answer based on image and text context."""
    req = VlmRequest(
        task=VlmTaskType.PAGE_UNDERSTANDING,
        prompt="What is the overall sales trend shown in the bar chart?",
        image_bytes=bar_chart_image_bytes,
        text_context="Context: Figure 3 - Quarterly Revenue Q1 to Q4.",
        output_format="text",
    )
    res = vlm_provider.analyze(req)

    assert res is not None
    assert res.text_result is not None
    assert "sales" in res.text_result.lower() or "chart" in res.text_result.lower()


# 4. Chart & Diagram Structured Analysis Test
def test_chart_and_diagram_structured_analysis(vlm_provider, bar_chart_image_bytes):
    """Verify structured VLM analysis returns validated JSON output dictionary."""
    req = VlmRequest(
        task=VlmTaskType.STRUCTURE_EXTRACTION,
        prompt="Extract structured elements from chart.",
        image_bytes=bar_chart_image_bytes,
        output_format="json",
    )
    res = vlm_provider.analyze(req)

    assert res is not None
    assert res.structured_result is not None
    assert isinstance(res.structured_result, dict)
    assert "summary" in res.structured_result


# 5. ModelManager Spec Lifecycle Test for smolvlm_local
def test_model_manager_vlm_spec_lifecycle():
    """Verify smolvlm_local is registered in ModelRegistry for TaskType.VLM."""
    mgr = default_model_manager
    models = mgr.list_available_models(task=TaskType.VLM)

    vlm_ids = [m.model_id for m in models]
    assert "smolvlm_local" in vlm_ids
