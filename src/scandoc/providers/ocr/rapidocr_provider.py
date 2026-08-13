"""
RapidOCR provider implementation wrapping Baidu PP-OCRv4 via RapidOCR ONNX runtime.
"""

import io
import logging
import time
from pathlib import Path
from typing import BinaryIO, List, Optional, Union

from PIL import Image

from scandoc.models.geometry import BoundingBox, CoordOrigin, Point2D, SizeUnit
from scandoc.providers.ocr.base import BaseOcrProvider
from scandoc.providers.ocr.exceptions import (
    InvalidImageError,
    OcrInferenceError,
    OcrInitializationError,
    OcrProviderUnavailableError,
    UnsupportedImageFormatError,
)
from scandoc.providers.ocr.models import OcrConfig, OCRResult, OCRTextRegion

logger = logging.getLogger("scandoc.providers.ocr.rapidocr")


class RapidOCRProvider(BaseOcrProvider):
    """
    RapidOCR Provider baseline candidate.
    
    Executes PP-OCRv4 detection and recognition models using ONNX Runtime.
    All RapidOCR-specific dependencies remain strictly isolated inside this provider module.
    """

    def __init__(self, config: Optional[OcrConfig] = None):
        self._engine = None
        self._config = config or OcrConfig()
        self._initialized = False

    @property
    def provider_id(self) -> str:
        return "rapidocr"

    @property
    def model_id(self) -> str:
        return "PP-OCRv4"

    @property
    def supported_languages(self) -> List[str]:
        return ["en", "ch", "es", "fr", "de", "ja", "ko"]

    @property
    def is_available(self) -> bool:
        """Return True if rapidocr_onnxruntime or rapidocr is installed."""
        try:
            import rapidocr_onnxruntime  # type: ignore
            return True
        except ImportError:
            try:
                import rapidocr  # type: ignore
                return True
            except ImportError:
                return False

    def initialize(self, config: Optional[OcrConfig] = None) -> None:
        if config is not None:
            self._config = config

        if not self.is_available:
            raise OcrProviderUnavailableError(
                "RapidOCR engine is not installed. Install 'rapidocr_onnxruntime' to use RapidOCRProvider."
            )

        try:
            try:
                from rapidocr_onnxruntime import RapidOCR
            except ImportError:
                from rapidocr import RapidOCR  # type: ignore

            self._engine = RapidOCR()
            self._initialized = True
            logger.info("RapidOCRProvider initialized successfully with model %s", self.model_id)
        except Exception as e:
            logger.error("Failed to initialize RapidOCR engine: %s", e)
            raise OcrInitializationError(f"RapidOCR initialization failed: {e}") from e

    def process_image(
        self,
        image_input: Union[str, Path, bytes, bytearray, BinaryIO],
        config: Optional[OcrConfig] = None,
    ) -> OCRResult:
        if not self._initialized:
            self.initialize(config=config)

        if self._engine is None:
            raise OcrProviderUnavailableError("RapidOCR engine instance is not initialized")

        effective_config = config or self._config

        # Step 1: Load Image & Get Dimensions
        img_bytes, img_width, img_height = self._load_image(image_input)

        # Step 2: Run RapidOCR Inference
        start_time = time.perf_counter()
        try:
            ocr_output = self._engine(img_bytes)
        except Exception as e:
            logger.error("RapidOCR inference failed: %s", e)
            raise OcrInferenceError(f"RapidOCR inference execution failed: {e}") from e

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Step 3: Parse Regions & Convert Bounding Boxes
        result = None
        if hasattr(ocr_output, "boxes") and hasattr(ocr_output, "txts") and hasattr(ocr_output, "scores"):
            boxes = getattr(ocr_output, "boxes", None)
            txts = getattr(ocr_output, "txts", None)
            scores = getattr(ocr_output, "scores", None)
            if boxes is not None and txts is not None and scores is not None:
                result = [
                    [box, txt, score]
                    for box, txt, score in zip(boxes, txts, scores)
                ]
        elif isinstance(ocr_output, (list, tuple)):
            if len(ocr_output) >= 2:
                result = ocr_output[0]
            else:
                result = ocr_output
        regions: List[OCRTextRegion] = []
        full_text_parts: List[str] = []

        if result:
            for reg_idx, item in enumerate(result):
                # item structure in RapidOCR: [polygon_pts, text, confidence]
                try:
                    poly_pts, text_str, conf = item[0], str(item[1]), float(item[2])
                except (IndexError, TypeError, ValueError):
                    continue

                if conf < effective_config.confidence_threshold:
                    continue

                full_text_parts.append(text_str)

                # Extract polygon points and calculate normalized bbox
                polygon: List[Point2D] = []
                min_x, min_y = float("inf"), float("inf")
                max_x, max_y = float("-inf"), float("-inf")

                for pt in poly_pts:
                    px, py = float(pt[0]), float(pt[1])
                    polygon.append(Point2D(x=px, y=py))
                    min_x = min(min_x, px)
                    min_y = min(min_y, py)
                    max_x = max(max_x, px)
                    max_y = max(max_y, py)

                norm_l = max(0.0, min(1.0, min_x / img_width))
                norm_t = max(0.0, min(1.0, min_y / img_height))
                norm_r = max(0.0, min(1.0, max_x / img_width))
                norm_b = max(0.0, min(1.0, max_y / img_height))

                if norm_l > norm_r:
                    norm_l, norm_r = norm_r, norm_l
                if norm_t > norm_b:
                    norm_t, norm_b = norm_b, norm_t

                bbox = BoundingBox(
                    left=round(norm_l, 5),
                    top=round(norm_t, 5),
                    right=round(norm_r, 5),
                    bottom=round(norm_b, 5),
                    coord_origin=CoordOrigin.TOP_LEFT,
                    unit=SizeUnit.NORMALIZED,
                    is_normalized=True,
                )

                regions.append(
                    OCRTextRegion(
                        text=text_str,
                        bbox=bbox,
                        polygon=polygon,
                        confidence=round(conf, 4),
                        region_idx=reg_idx,
                    )
                )

        full_text = "\n".join(full_text_parts)

        return OCRResult(
            full_text=full_text,
            regions=regions,
            provider_id=self.provider_id,
            model_id=self.model_id,
            image_width=img_width,
            image_height=img_height,
            processing_time_ms=round(elapsed_ms, 2),
        )

    def _load_image(
        self, image_input: Union[str, Path, bytes, bytearray, BinaryIO]
    ) -> tuple[bytes, int, int]:
        """Load input image and return raw bytes, width_px, height_px."""
        try:
            if isinstance(image_input, (str, Path)):
                path_obj = Path(image_input)
                if not path_obj.exists():
                    raise InvalidImageError(f"Image file not found: {image_input}")
                img_bytes = path_obj.read_bytes()
            elif isinstance(image_input, (bytes, bytearray)):
                img_bytes = bytes(image_input)
            elif hasattr(image_input, "read"):
                img_bytes = image_input.read()
            else:
                raise InvalidImageError(f"Unsupported image input type: {type(image_input)}")

            if len(img_bytes) == 0:
                raise InvalidImageError("Input image source is 0 bytes")

            # Open image with PIL to verify format and read dimensions
            with Image.open(io.BytesIO(img_bytes)) as pil_img:
                width, height = pil_img.size
                if pil_img.format and pil_img.format.upper() not in (
                    "PNG", "JPEG", "JPG", "WEBP", "TIFF", "TIF", "BMP"
                ):
                    raise UnsupportedImageFormatError(f"Unsupported image format: {pil_img.format}")

            return img_bytes, width, height

        except (InvalidImageError, UnsupportedImageFormatError):
            raise
        except Exception as e:
            raise InvalidImageError(f"Failed to decode or inspect image: {e}") from e

    def shutdown(self) -> None:
        self._engine = None
        self._initialized = False
