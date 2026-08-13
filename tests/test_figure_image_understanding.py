"""
Unit and integration test suite for Phase 12: Figure, Image & Caption Understanding.
"""

import io
import pytest
from PIL import Image

from scandoc.models.blocks import CaptionBlock, FigureBlock
from scandoc.models.geometry import BoundingBox
from scandoc.models.provenance import ProcessingStage, Provenance
from scandoc.providers.figures import (
    BaseFigureProvider,
    CaptionAssociator,
    FigureConfig,
    FigureProviderRegistry,
    FigureResult,
    FigureType,
    GenericRemoteFigureProvider,
    HuggingFaceFigureAdapter,
    ImageInput,
    LocalFigureProvider,
    ProviderType,
    figure_result_to_document_ir,
    InvalidImageInputError,
    PrivacyViolationError,
)


def create_sample_image_bytes(width=200, height=100, fmt="PNG") -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color=(100, 150, 200)).save(buf, format=fmt)
    return buf.getvalue()


def test_figure_result_and_image_input_validation():
    """Test ImageInput and FigureResult data model validation."""
    img_bytes = create_sample_image_bytes(200, 100, "PNG")
    inp = ImageInput(
        source_type="embedded",
        image_bytes=img_bytes,
        page_index=0,
        bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.5, is_normalized=True),
    )
    assert inp.source_type == "embedded"

    prov = LocalFigureProvider()
    res = prov.analyze_figure(inp)

    assert isinstance(res, FigureResult)
    assert res.metadata["width"] == "200"
    assert res.metadata["height"] == "100"
    assert res.metadata["format"] == "PNG"
    assert float(res.metadata["aspect_ratio"]) == 2.0


def test_caption_associator():
    """Test CaptionAssociator linking captions above/below figures based on spatial distance."""
    fig_res = FigureResult(
        figure_id="fig_1",
        page_index=0,
        bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.4, is_normalized=True),
        provider_id="test_p",
        model_id="test_m",
    )

    # Caption block below figure
    cap_block = CaptionBlock(
        id="cap_1",
        text="Figure 1: Test Architecture Diagram",
        bbox=BoundingBox(left=0.1, top=0.42, right=0.9, bottom=0.45, is_normalized=True),
        provenance=Provenance(provider="test", stage=ProcessingStage.NATIVE_EXTRACTION),
    )

    associated = CaptionAssociator.associate_captions([fig_res], [cap_block], max_distance=0.08)
    assert len(associated) == 1
    assert associated[0].associated_caption_id == "cap_1"
    assert associated[0].associated_caption_text == "Figure 1: Test Architecture Diagram"


def test_figure_without_caption_and_unmatched_caption():
    """Test figures without captions and unassociated captions."""
    fig_res = FigureResult(
        figure_id="fig_standalone",
        page_index=0,
        bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.4, is_normalized=True),
        provider_id="test_p",
        model_id="test_m",
    )

    # Far away caption block (vertical gap > 0.20)
    cap_far = CaptionBlock(
        id="cap_far",
        text="Figure 99: Far Away",
        bbox=BoundingBox(left=0.1, top=0.8, right=0.9, bottom=0.85, is_normalized=True),
        provenance=Provenance(provider="test", stage=ProcessingStage.NATIVE_EXTRACTION),
    )

    associated = CaptionAssociator.associate_captions([fig_res], [cap_far], max_distance=0.08)
    assert associated[0].associated_caption_id is None


def test_privacy_remote_provider_enforcement():
    """Security Test: Remote figure providers MUST raise PrivacyViolationError if allow_remote=False."""
    remote_prov = GenericRemoteFigureProvider(
        config=FigureConfig(
            endpoint="https://api.cloud-vision.internal/v1/analyze",
            allow_remote=False,
        )
    )

    inp = ImageInput(image_bytes=create_sample_image_bytes())

    # Verify initialize and analyze_figure raise PrivacyViolationError
    with pytest.raises(PrivacyViolationError):
        remote_prov.initialize()

    with pytest.raises(PrivacyViolationError):
        remote_prov.analyze_figure(inp)


def test_figure_provider_registry():
    """Test FigureProviderRegistry registration and selection."""
    registry = FigureProviderRegistry(register_defaults=True)
    assert len(registry.list_providers()) == 3

    # Default selection returns local provider
    local_p = registry.select_provider(FigureConfig(allow_remote=False))
    assert local_p.provider_type == ProviderType.LOCAL


def test_figure_result_to_document_ir_conversion():
    """Test converting FigureResult into DocumentIR FigureBlock model."""
    fig_res = FigureResult(
        figure_id="fig_ir_1",
        page_index=0,
        bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.5, is_normalized=True),
        figure_type=FigureType.DIAGRAM,
        associated_caption_id="cap_1",
        associated_caption_text="Figure 1: IR Test Diagram",
        provider_id="local_figure_analyzer",
        model_id="BasicFigureAnalyzer-v1",
    )

    fig_block: FigureBlock = figure_result_to_document_ir(fig_res)
    assert isinstance(fig_block, FigureBlock)
    assert fig_block.id == "fig_ir_1"
    assert fig_block.caption == "Figure 1: IR Test Diagram"
    assert fig_block.provenance.provider == "local_figure_analyzer"


def test_invalid_image_input_error():
    """Test InvalidImageInputError when ImageInput contains empty payload."""
    inp = ImageInput()
    prov = LocalFigureProvider()

    with pytest.raises(InvalidImageInputError):
        prov.analyze_figure(inp)
