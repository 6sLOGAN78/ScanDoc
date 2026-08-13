"""
Preprocessing pipeline engine, PreprocessedImage container, and adaptive pipeline builder.
"""

import io
from pathlib import Path
import time
from typing import BinaryIO, Dict, List, Optional, Union
from PIL import Image
from pydantic import BaseModel, Field

from scandoc.image.analysis import ImageAnalysis, ImageAnalyzer
from scandoc.image.exceptions import InvalidImageInputError, PreprocessingError
from scandoc.image.operations import (
    AdaptiveThresholdOp,
    BaseImageOp,
    ContrastBrightnessOp,
    CropBorderOp,
    DenoiseOp,
    DeskewOp,
    GrayscaleOp,
    ResizeDpiOp,
    RotateOp,
    SharpenOp,
)


class PreprocessedImage(BaseModel):
    """
    Container preserving original input bytes, processed image bytes, and processing metadata.
    """
    original_bytes: bytes = Field(..., description="Unmodified raw input image bytes")
    processed_bytes: bytes = Field(..., description="Processed PNG image bytes ready for OCR")
    width: int = Field(..., ge=1, description="Pixel width of final processed image")
    height: int = Field(..., ge=1, description="Pixel height of final processed image")
    analysis: ImageAnalysis = Field(..., description="Initial image quality analysis summary")
    operations_applied: List[str] = Field(default_factory=list, description="Sequence of preprocessing operations applied")
    processing_time_ms: float = Field(0.0, ge=0.0, description="Total preprocessing latency in milliseconds")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Arbitrary pipeline metadata")


class PreprocessingPipeline:
    """
    Composable image preprocessing pipeline executing sequential operations over document images.
    """

    def __init__(self, operations: Optional[List[BaseImageOp]] = None):
        self.operations: List[BaseImageOp] = operations or []

    def add_operation(self, op: BaseImageOp) -> "PreprocessingPipeline":
        """Append an operation to the pipeline."""
        self.operations.append(op)
        return self

    def clear(self) -> None:
        """Clear all operations."""
        self.operations.clear()

    def process(
        self, image_input: Union[str, Path, bytes, bytearray, BinaryIO]
    ) -> PreprocessedImage:
        """
        Analyze image, execute pipeline operations sequentially, and return PreprocessedImage.
        
        Args:
            image_input: File path, bytes buffer, or binary stream.
            
        Returns:
            PreprocessedImage preserving original bytes and processed PNG bytes.
        """
        # Step 1: Initial Image Analysis
        analysis = ImageAnalyzer.analyze(image_input)
        img, original_bytes = ImageAnalyzer._load_pil_image(image_input)

        start_time = time.perf_counter()
        current_img = img
        applied_ops: List[str] = []

        # Step 2: Sequential Operations Execution
        for op in self.operations:
            try:
                current_img = op.apply(current_img)
                applied_ops.append(op.name)
            except Exception as e:
                raise PreprocessingError(f"Operation '{op.name}' failed: {e}") from e

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Step 3: Encode Processed Image to PNG Bytes
        out_buf = io.BytesIO()
        current_img.save(out_buf, format="PNG")
        processed_bytes = out_buf.getvalue()

        out_width, out_height = current_img.size

        return PreprocessedImage(
            original_bytes=original_bytes,
            processed_bytes=processed_bytes,
            width=out_width,
            height=out_height,
            analysis=analysis,
            operations_applied=applied_ops,
            processing_time_ms=round(elapsed_ms, 2),
        )


class AdaptivePipelineBuilder:
    """
    Deterministic adaptive pipeline builder selecting preprocessing operations
    based on ImageAnalysis characteristics.
    """

    @classmethod
    def build_pipeline(cls, analysis: ImageAnalysis) -> PreprocessingPipeline:
        """
        Construct an optimal PreprocessingPipeline based on image characteristics.
        """
        ops: List[BaseImageOp] = []

        # 1. Orientation & Deskew
        if analysis.is_skewed:
            ops.append(DeskewOp(angle_deg=analysis.skew_angle_deg))

        # 2. Resolution Normalization
        if analysis.is_low_res:
            ops.append(ResizeDpiOp(target_dpi=300, min_width=1200))
            ops.append(SharpenOp())

        # 3. Grayscale conversion
        if analysis.color_mode != "L":
            ops.append(GrayscaleOp())

        # 4. Contrast & Denoise for scans
        if analysis.is_low_contrast or analysis.is_noisy:
            if analysis.is_noisy:
                ops.append(DenoiseOp(size=3))
            if analysis.is_low_contrast:
                ops.append(ContrastBrightnessOp(contrast_factor=1.4, brightness_factor=1.05))
            ops.append(AdaptiveThresholdOp(block_size=15, C=10))

        # Fallback to minimal grayscale if clean digital render
        if not ops:
            ops.append(GrayscaleOp())

        return PreprocessingPipeline(operations=ops)
