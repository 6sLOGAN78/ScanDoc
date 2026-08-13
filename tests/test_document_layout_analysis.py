"""
Unit and integration test suite for Phase 9: Document Layout Analysis.
"""

from typing import BinaryIO, List, Optional, Union
import pytest

from scandoc.models import DocumentIR
from scandoc.models.blocks import HeadingBlock, ParagraphBlock, TableBlock, FigureBlock
from scandoc.models.geometry import BoundingBox, CoordOrigin, SizeUnit
from scandoc.models.provenance import ProcessingStage
from scandoc.providers.layout import (
    BaseLayoutProvider,
    DocLayNetMapper,
    LayoutCategory,
    LayoutConfig,
    LayoutProviderRegistry,
    LayoutRegion,
    LayoutResult,
    PubLayNetMapper,
    RtDetrLayoutProvider,
    layout_result_to_document_ir,
    LayoutProviderUnavailableError,
)


class MockLayoutProvider(BaseLayoutProvider):
    """Mock layout provider for deterministic testing without external weights."""

    @property
    def provider_id(self) -> str:
        return "mock_layout_provider"

    @property
    def model_id(self) -> str:
        return "Mock-DocLayNet-v1"

    @property
    def supported_categories(self) -> List[LayoutCategory]:
        return [LayoutCategory.TITLE, LayoutCategory.PARAGRAPH, LayoutCategory.TABLE, LayoutCategory.FIGURE]

    def initialize(self, config: Optional[LayoutConfig] = None) -> None:
        pass

    def detect_layout(
        self,
        image_input: Union[str, bytes, bytearray, BinaryIO],
        page_index: int = 0,
        config: Optional[LayoutConfig] = None,
    ) -> LayoutResult:
        regions = [
            LayoutRegion(
                category=LayoutCategory.TITLE,
                confidence=0.98,
                bbox=BoundingBox(left=0.1, top=0.05, right=0.9, bottom=0.15, is_normalized=True),
                page_index=page_index,
                region_idx=0,
            ),
            LayoutRegion(
                category=LayoutCategory.PARAGRAPH,
                confidence=0.92,
                bbox=BoundingBox(left=0.1, top=0.20, right=0.9, bottom=0.45, is_normalized=True),
                page_index=page_index,
                region_idx=1,
            ),
            LayoutRegion(
                category=LayoutCategory.TABLE,
                confidence=0.95,
                bbox=BoundingBox(left=0.1, top=0.50, right=0.9, bottom=0.85, is_normalized=True),
                page_index=page_index,
                region_idx=2,
            ),
        ]
        return LayoutResult(
            regions=regions,
            provider_id=self.provider_id,
            model_id=self.model_id,
            image_width=1000,
            image_height=1400,
            page_index=page_index,
            processing_time_ms=12.5,
        )


def test_layout_region_and_result_validation():
    """Test LayoutRegion and LayoutResult Pydantic schema validation."""
    bbox = BoundingBox(left=0.1, top=0.1, right=0.5, bottom=0.5, is_normalized=True)
    region = LayoutRegion(
        category=LayoutCategory.TITLE,
        confidence=0.965,
        bbox=bbox,
        page_index=0,
        region_idx=0,
    )
    assert region.category == LayoutCategory.TITLE
    assert region.confidence == 0.965

    res = LayoutResult(
        regions=[region],
        provider_id="test_provider",
        model_id="test_model",
        image_width=800,
        image_height=1000,
        page_index=0,
    )
    assert len(res.regions) == 1
    assert res.regions[0].category == LayoutCategory.TITLE


def test_taxonomy_class_mappers():
    """Test DocLayNetMapper and PubLayNetMapper converting model IDs to LayoutCategory."""
    assert DocLayNetMapper.map_class(10) == LayoutCategory.TITLE
    assert DocLayNetMapper.map_class(8) == LayoutCategory.TABLE
    assert DocLayNetMapper.map_class(0) == LayoutCategory.CAPTION
    assert DocLayNetMapper.map_class("list_item") == LayoutCategory.LIST
    assert DocLayNetMapper.map_class(999) == LayoutCategory.UNKNOWN

    assert PubLayNetMapper.map_class(1) == LayoutCategory.TITLE
    assert PubLayNetMapper.map_class(3) == LayoutCategory.TABLE
    assert PubLayNetMapper.map_class("figure") == LayoutCategory.FIGURE


def test_layout_coordinate_normalization():
    """Test normalized bounding box coordinate scaling and portrait/landscape handling."""
    # Portrait Page 1000 x 2000 px: (100, 200, 900, 1800) -> (0.1, 0.1, 0.9, 0.9)
    box_portrait = BoundingBox(
        left=100 / 1000, top=200 / 2000, right=900 / 1000, bottom=1800 / 2000, is_normalized=True
    )
    assert box_portrait.left == 0.1
    assert box_portrait.top == 0.1
    assert box_portrait.right == 0.9
    assert box_portrait.bottom == 0.9

    # Landscape Page 2000 x 1000 px: (200, 100, 1800, 900) -> (0.1, 0.1, 0.9, 0.9)
    box_landscape = BoundingBox(
        left=200 / 2000, top=100 / 1000, right=1800 / 2000, bottom=900 / 1000, is_normalized=True
    )
    assert box_landscape.left == 0.1
    assert box_landscape.top == 0.1
    assert box_landscape.right == 0.9
    assert box_landscape.bottom == 0.9


def test_layout_provider_registry():
    """Test LayoutProviderRegistry registration and lookup."""
    registry = LayoutProviderRegistry(register_defaults=False)
    mock_p = MockLayoutProvider()
    registry.register(mock_p)

    assert len(registry.list_providers()) == 1
    retrieved = registry.get_provider("mock_layout_provider")
    assert retrieved.provider_id == "mock_layout_provider"

    selected = registry.select_provider()
    assert selected.provider_id == "mock_layout_provider"


def test_rt_detr_provider_available_check():
    """Test RtDetrLayoutProvider availability reporting and missing model error."""
    provider = RtDetrLayoutProvider(config=LayoutConfig(model_path="/non_existent/model.onnx"))
    assert provider.provider_id == "rt_detr_layout"
    assert provider.is_available is False

    with pytest.raises(LayoutProviderUnavailableError):
        provider.initialize()


def test_layout_result_to_document_ir_conversion():
    """Test converting LayoutResult predictions to DocumentIR blocks."""
    mock_p = MockLayoutProvider()
    layout_res = mock_p.detect_layout(b"fake_image_bytes", page_index=0)

    doc: DocumentIR = layout_result_to_document_ir(layout_res)
    assert len(doc.pages) == 1
    page = doc.pages[0]
    assert len(page.blocks) == 3

    # Check Block 0: HeadingBlock (Title)
    b0 = page.blocks[0]
    assert isinstance(b0, HeadingBlock)
    assert b0.level == 1
    assert b0.provenance is not None
    assert b0.provenance.provider == "mock_layout_provider"
    assert b0.provenance.stage == ProcessingStage.LAYOUT_ANALYSIS

    # Check Block 1: ParagraphBlock
    b1 = page.blocks[1]
    assert isinstance(b1, ParagraphBlock)

    # Check Block 2: TableBlock
    b2 = page.blocks[2]
    assert isinstance(b2, TableBlock)
