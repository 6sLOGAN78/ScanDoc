"""
Unit test suite for Phase 5: OCR Engine Foundation & RapidOCR Baseline Provider.
"""

import io
from typing import BinaryIO, List, Optional, Union
import pytest
from PIL import Image, ImageDraw, ImageFont

from scandoc.models import BlockType, DocumentIR, ProcessingStage
from scandoc.models.geometry import BoundingBox, Point2D
from scandoc.providers.ocr import (
    BaseOcrProvider,
    OcrConfig,
    OCRResult,
    OCRTextRegion,
    RapidOCRProvider,
    ocr_result_to_document_ir,
    InvalidImageError,
    UnsupportedImageFormatError,
    OcrProviderUnavailableError,
    OcrError,
)


class MockOcrProvider(BaseOcrProvider):
    """
    Deterministic Mock OCR Provider for offline unit testing without model weights or network access.
    """

    def __init__(self, mock_regions: Optional[List[OCRTextRegion]] = None):
        self._mock_regions = mock_regions or []
        self._initialized = False

    @property
    def provider_id(self) -> str:
        return "mock_ocr"

    @property
    def model_id(self) -> str:
        return "Mock-v1"

    @property
    def supported_languages(self) -> List[str]:
        return ["en"]

    def initialize(self, config: Optional[OcrConfig] = None) -> None:
        self._initialized = True

    def process_image(
        self,
        image_input: Union[str, bytes, bytearray, BinaryIO],
        config: Optional[OcrConfig] = None,
    ) -> OCRResult:
        full_text = "\n".join(r.text for r in self._mock_regions)
        return OCRResult(
            full_text=full_text,
            regions=self._mock_regions,
            provider_id=self.provider_id,
            model_id=self.model_id,
            image_width=800,
            image_height=600,
            processing_time_ms=5.0,
        )


def create_test_image_bytes(text: str = "SCAN DOC TEST OCR") -> bytes:
    """Helper creating an in-memory PNG image with black text on white background."""
    img = Image.new("RGB", (400, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 35), text, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_ocr_text_region_validation():
    """Test OCRTextRegion spatial properties and confidence validation."""
    bbox = BoundingBox(left=0.1, top=0.2, right=0.9, bottom=0.4, is_normalized=True)
    poly = [Point2D(x=40, y=20), Point2D(x=360, y=20), Point2D(x=360, y=40), Point2D(x=40, y=40)]
    
    region = OCRTextRegion(
        text="Sample OCR Text",
        bbox=bbox,
        polygon=poly,
        confidence=0.95,
        region_idx=0,
    )
    assert region.text == "Sample OCR Text"
    assert region.confidence == 0.95
    assert len(region.polygon) == 4

    # Invalid confidence bounds check
    with pytest.raises(Exception):
        OCRTextRegion(text="Err", bbox=bbox, confidence=1.5)


def test_ocr_result_schema():
    """Test OCRResult container metadata."""
    bbox = BoundingBox(left=0.0, top=0.0, right=1.0, bottom=0.5, is_normalized=True)
    reg = OCRTextRegion(text="Line 1", bbox=bbox, confidence=0.9)
    
    res = OCRResult(
        full_text="Line 1",
        regions=[reg],
        provider_id="rapidocr",
        model_id="PP-OCRv4",
        image_width=1000,
        image_height=500,
        processing_time_ms=12.5,
    )
    assert res.provider_id == "rapidocr"
    assert res.model_id == "PP-OCRv4"
    assert len(res.regions) == 1
    assert res.image_width == 1000


def test_mock_ocr_provider_execution():
    """Test BaseOcrProvider interface compliance via MockOcrProvider."""
    bbox = BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.3)
    mock_reg = OCRTextRegion(text="Deterministic Text Line", bbox=bbox, confidence=0.98)
    
    provider = MockOcrProvider(mock_regions=[mock_reg])
    assert provider.provider_id == "mock_ocr"
    assert provider.model_id == "Mock-v1"
    
    res = provider.process_image(b"fake_image_bytes")
    assert res.full_text == "Deterministic Text Line"
    assert len(res.regions) == 1
    assert res.regions[0].confidence == 0.98


def test_ocr_result_to_document_ir_conversion():
    """Test converting OCRResult into DocumentIR."""
    bbox = BoundingBox(left=0.1, top=0.1, right=0.8, bottom=0.3)
    reg1 = OCRTextRegion(text="Header Line", bbox=bbox, confidence=0.96, region_idx=0)
    reg2 = OCRTextRegion(text="Paragraph Line", bbox=bbox, confidence=0.92, region_idx=1)
    
    ocr_res = OCRResult(
        full_text="Header Line\nParagraph Line",
        regions=[reg1, reg2],
        provider_id="rapidocr",
        model_id="PP-OCRv4",
        image_width=1000,
        image_height=800,
    )
    
    doc: DocumentIR = ocr_result_to_document_ir(ocr_res, page_index=0, doc_id="doc-ocr-1")
    
    assert isinstance(doc, DocumentIR)
    assert doc.metadata.id == "doc-ocr-1"
    assert len(doc.pages) == 1
    assert doc.pages[0].width == 1000.0
    assert doc.pages[0].height == 800.0
    assert len(doc.pages[0].blocks) == 2
    
    blk0 = doc.pages[0].blocks[0]
    assert blk0.block_type == BlockType.TEXT
    assert blk0.text == "Header Line"
    assert blk0.provenance.provider == "rapidocr"
    assert blk0.provenance.model == "PP-OCRv4"
    assert blk0.provenance.stage == ProcessingStage.OCR
    assert blk0.provenance.confidence == 0.96


def test_rapidocr_provider_metadata_and_availability():
    """Test RapidOCRProvider metadata properties and is_available reporting."""
    provider = RapidOCRProvider()
    assert provider.provider_id == "rapidocr"
    assert provider.model_id == "PP-OCRv4"
    assert "en" in provider.supported_languages
    assert isinstance(provider.is_available, bool)


def test_rapidocr_invalid_image_errors():
    """Test RapidOCRProvider image error handling."""
    provider = RapidOCRProvider()
    
    # 0-byte image error
    with pytest.raises(InvalidImageError):
        provider.process_image(b"")

    # Corrupt/unreadable image error
    with pytest.raises(InvalidImageError):
        provider.process_image(b"CORRUPTED_NOT_AN_IMAGE")


def test_rapidocr_unsupported_format_error(tmp_path):
    """Test loading unsupported image extension raises UnsupportedImageFormatError."""
    provider = RapidOCRProvider()
    bad_img = tmp_path / "test.unsupported_ext"
    bad_img.write_bytes(b"some random non-image bytes")
    
    with pytest.raises(OcrError):
        provider.process_image(str(bad_img))


@pytest.mark.skipif(
    not RapidOCRProvider().is_available,
    reason="rapidocr_onnxruntime is not installed in the environment"
)
def test_live_rapidocr_image_inference():
    """Live integration test executing RapidOCR ONNX model when rapidocr is available."""
    img_bytes = create_test_image_bytes("SAMPLE OCR LINE")
    provider = RapidOCRProvider()
    
    res = provider.process_image(img_bytes)
    assert res.provider_id == "rapidocr"
    assert res.image_width == 400
    assert res.image_height == 100
    assert isinstance(res.processing_time_ms, float)
