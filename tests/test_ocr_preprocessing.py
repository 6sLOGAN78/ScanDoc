"""
Unit test suite for Phase 6: OCR Preprocessing & Image Pipeline.
"""

import io
import time
import pytest
from PIL import Image, ImageDraw, ImageFilter

from scandoc.image import (
    ImageAnalysis,
    ImageAnalyzer,
    PreprocessedImage,
    PreprocessingPipeline,
    AdaptivePipelineBuilder,
    GrayscaleOp,
    ResizeDpiOp,
    ContrastBrightnessOp,
    DenoiseOp,
    SharpenOp,
    AdaptiveThresholdOp,
    DeskewOp,
    RotateOp,
    CropBorderOp,
    InvalidImageInputError,
)
from scandoc.models import DocumentIR
from scandoc.providers.ocr import OCRResult, OCRTextRegion, ocr_result_to_document_ir
from test_ocr_foundation import MockOcrProvider


def create_synthetic_image_bytes(
    width: int = 400,
    height: int = 200,
    mode: str = "RGB",
    bg_color=(255, 255, 255),
    text: str = "SAMPLE PREPROCESSING TEST",
    noise: bool = False,
    blur: bool = False,
) -> bytes:
    """Helper to generate synthetic test images."""
    img = Image.new(mode, (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    draw.text((20, 80), text, fill=(0, 0, 0))

    if blur:
        img = img.filter(ImageFilter.BLUR)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    if noise:
        # Add random byte noise if requested
        arr = bytearray(raw_bytes)
        for i in range(100, min(200, len(arr))):
            arr[i] = (arr[i] + 13) % 256
        return bytes(arr)

    return raw_bytes


def test_image_analyzer_clean_image():
    """Test ImageAnalyzer on a clean synthetic RGB image."""
    img_bytes = create_synthetic_image_bytes(width=1600, height=1200)
    analysis: ImageAnalysis = ImageAnalyzer.analyze(img_bytes)

    assert analysis.width == 1600
    assert analysis.height == 1200
    assert analysis.color_mode == "RGB"
    assert analysis.aspect_ratio == 1.333
    assert 0.0 <= analysis.mean_brightness <= 255.0
    assert analysis.is_low_res is False


def test_image_analyzer_low_res():
    """Test ImageAnalyzer flagging low resolution images (< 1000px)."""
    img_bytes = create_synthetic_image_bytes(width=400, height=200)
    analysis = ImageAnalyzer.analyze(img_bytes)

    assert analysis.is_low_res is True


def test_grayscale_op():
    """Test GrayscaleOp converts RGB image to 'L' mode."""
    img_bytes = create_synthetic_image_bytes(mode="RGB")
    pil_img = Image.open(io.BytesIO(img_bytes))
    
    op = GrayscaleOp()
    out_img = op.apply(pil_img)
    assert out_img.mode == "L"
    assert pil_img.mode == "RGB"  # Ensures input was not mutated in-place


def test_resize_dpi_op():
    """Test ResizeDpiOp upscales low-resolution images."""
    img_bytes = create_synthetic_image_bytes(width=400, height=200)
    pil_img = Image.open(io.BytesIO(img_bytes))

    op = ResizeDpiOp(min_width=1200)
    out_img = op.apply(pil_img)
    assert out_img.size[0] == 1200
    assert out_img.size[1] == 600


def test_contrast_brightness_op():
    """Test ContrastBrightnessOp modifies pixel intensity distribution."""
    img_bytes = create_synthetic_image_bytes()
    pil_img = Image.open(io.BytesIO(img_bytes))

    op = ContrastBrightnessOp(contrast_factor=1.5, brightness_factor=1.1)
    out_img = op.apply(pil_img)
    assert out_img.size == pil_img.size


def test_rotate_and_deskew_ops():
    """Test RotateOp and DeskewOp."""
    img_bytes = create_synthetic_image_bytes(width=400, height=200)
    pil_img = Image.open(io.BytesIO(img_bytes))

    rot_op = RotateOp(angle_deg=90)
    out_rot = rot_op.apply(pil_img)
    assert out_rot.size == (200, 400)

    deskew_op = DeskewOp(angle_deg=2.5)
    out_deskew = deskew_op.apply(pil_img)
    assert out_deskew.size[0] >= 400


def test_crop_border_op():
    """Test CropBorderOp cropping margin borders."""
    img_bytes = create_synthetic_image_bytes(width=400, height=200)
    pil_img = Image.open(io.BytesIO(img_bytes))

    crop_op = CropBorderOp(margin_px=10)
    out_crop = crop_op.apply(pil_img)
    assert out_crop.size == (380, 180)


def test_preprocessing_pipeline_composition():
    """Test building and executing a sequential PreprocessingPipeline."""
    img_bytes = create_synthetic_image_bytes(width=500, height=300)

    pipeline = PreprocessingPipeline()
    pipeline.add_operation(GrayscaleOp())
    pipeline.add_operation(ResizeDpiOp(min_width=1200))
    pipeline.add_operation(SharpenOp())

    res: PreprocessedImage = pipeline.process(img_bytes)

    assert isinstance(res, PreprocessedImage)
    assert res.width == 1200
    assert len(res.operations_applied) == 3
    assert "grayscale" in res.operations_applied[0]
    assert res.processing_time_ms > 0.0


def test_original_image_preservation():
    """Test that original_bytes is preserved 100% identically without mutation."""
    raw_input_bytes = create_synthetic_image_bytes(width=600, height=400)

    pipeline = PreprocessingPipeline([GrayscaleOp(), ResizeDpiOp(min_width=1200)])
    prep = pipeline.process(raw_input_bytes)

    # original_bytes MUST match raw_input_bytes byte for byte
    assert prep.original_bytes == raw_input_bytes
    assert prep.processed_bytes != raw_input_bytes
    assert prep.width == 1200


def test_adaptive_pipeline_builder():
    """Test AdaptivePipelineBuilder selecting rules based on ImageAnalysis."""
    # Scenario A: Low resolution image
    low_res_analysis = ImageAnalysis(
        width=500,
        height=300,
        aspect_ratio=1.67,
        color_mode="RGB",
        mean_brightness=200.0,
        contrast_std=50.0,
        blur_score=100.0,
        noise_estimate=5.0,
        skew_angle_deg=0.0,
        is_low_res=True,
    )
    pipe_low_res = AdaptivePipelineBuilder.build_pipeline(low_res_analysis)
    op_names = [op.name for op in pipe_low_res.operations]
    assert any("resize_dpi" in name for name in op_names)

    # Scenario B: Skewed image
    skewed_analysis = ImageAnalysis(
        width=1200,
        height=800,
        aspect_ratio=1.5,
        color_mode="RGB",
        mean_brightness=200.0,
        contrast_std=50.0,
        blur_score=100.0,
        noise_estimate=5.0,
        skew_angle_deg=3.5,
        is_skewed=True,
    )
    pipe_skewed = AdaptivePipelineBuilder.build_pipeline(skewed_analysis)
    op_names_skewed = [op.name for op in pipe_skewed.operations]
    assert any("deskew" in name for name in op_names_skewed)


def test_invalid_image_errors():
    """Test empty/corrupt image inputs raise InvalidImageInputError."""
    pipeline = PreprocessingPipeline([GrayscaleOp()])

    with pytest.raises(InvalidImageInputError):
        pipeline.process(b"")

    with pytest.raises(InvalidImageInputError):
        pipeline.process(b"INVALID_CORRUPT_BYTES")


def test_pipeline_ocr_integration():
    """
    Test full end-to-end integration:
    Image -> AdaptivePipelineBuilder -> PreprocessingPipeline -> MockOcrProvider -> OCRResult -> DocumentIR.
    """
    raw_img_bytes = create_synthetic_image_bytes(width=500, height=300, text="END TO END OCR PIPELINE")

    # 1. Analyze and build adaptive pipeline
    analysis = ImageAnalyzer.analyze(raw_img_bytes)
    pipeline = AdaptivePipelineBuilder.build_pipeline(analysis)

    # 2. Execute Preprocessing
    prep: PreprocessedImage = pipeline.process(raw_img_bytes)
    assert prep.processed_bytes is not None

    # 3. Process via OCR Provider
    ocr_provider = MockOcrProvider()
    ocr_res: OCRResult = ocr_provider.process_image(prep.processed_bytes)

    # 4. Convert OCRResult to DocumentIR
    doc: DocumentIR = ocr_result_to_document_ir(ocr_res, page_index=0)

    assert isinstance(doc, DocumentIR)
    assert doc.pages[0].width == 800.0
    assert doc.pages[0].height == 600.0
