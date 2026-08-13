"""
Tesseract OCR provider implementation wrapping pytesseract and Tesseract-OCR binary engine.
"""

import io
import logging
from pathlib import Path
import shutil
import time
from typing import BinaryIO, List, Optional, Union

from PIL import Image

from scandoc.models.geometry import BoundingBox, CoordOrigin, SizeUnit
from scandoc.providers.ocr.base import BaseOcrProvider
from scandoc.providers.ocr.exceptions import (
    InvalidImageError,
    OcrInferenceError,
    OcrInitializationError,
    OcrProviderUnavailableError,
    UnsupportedImageFormatError,
)
from scandoc.providers.ocr.models import OcrCapability, OcrProviderConfig, OCRResult, OCRTextRegion

logger = logging.getLogger("scandoc.providers.ocr.tesseract")


class TesseractProvider(BaseOcrProvider):
    """
    Tesseract OCR Engine Provider.
    
    Provides Tesseract optical character recognition when pytesseract and the system
    tesseract binary are available.
    """

    def __init__(self, config: Optional[OcrProviderConfig] = None):
        self._config = config or OcrProviderConfig(provider_name="tesseract", model_name="eng")
        self._initialized = False

    @property
    def provider_id(self) -> str:
        return "tesseract"

    @property
    def model_id(self) -> str:
        return self._config.language or "eng"

    @property
    def supported_languages(self) -> List[str]:
        return ["eng", "fra", "deu", "spa", "chi_sim", "jpn", "rus"]

    @property
    def capabilities(self) -> OcrCapability:
        return OcrCapability(
            provider_id=self.provider_id,
            is_local=True,
            supports_cpu=True,
            supports_gpu=False,
            supports_batch=False,
            supports_confidence=True,
            supports_polygons=False,
            supports_orientation=True,
            supported_languages=self.supported_languages,
        )

    @property
    def is_available(self) -> bool:
        """Return True if pytesseract python package and system tesseract binary exist."""
        if shutil.which("tesseract") is None:
            return False
        try:
            import pytesseract  # type: ignore
            return True
        except ImportError:
            return False

    def initialize(self, config: Optional[OcrProviderConfig] = None) -> None:
        if config is not None:
            self._config = config

        if not self.is_available:
            raise OcrProviderUnavailableError(
                "Tesseract OCR is not available. Install pytesseract and the 'tesseract' binary (e.g. apt-get install tesseract-ocr)."
            )
        self._initialized = True
        logger.info("TesseractProvider initialized with language model '%s'", self.model_id)

    def process_image(
        self,
        image_input: Union[str, Path, bytes, bytearray, BinaryIO],
        config: Optional[OcrProviderConfig] = None,
    ) -> OCRResult:
        if not self._initialized:
            self.initialize(config=config)

        if not self.is_available:
            raise OcrProviderUnavailableError("Tesseract OCR engine is not available")

        import pytesseract  # type: ignore
        from pytesseract import Output  # type: ignore

        effective_config = config or self._config

        # Step 1: Read image
        img_bytes, width, height = self._load_image(image_input)
        pil_img = Image.open(io.BytesIO(img_bytes))

        # Step 2: Run Tesseract Inference
        start_time = time.perf_counter()
        try:
            data = pytesseract.image_to_data(
                pil_img,
                lang=effective_config.language or "eng",
                output_type=Output.DICT
            )
        except Exception as e:
            raise OcrInferenceError(f"Tesseract OCR execution failed: {e}") from e

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Step 3: Parse word/line regions
        regions: List[OCRTextRegion] = []
        full_text_parts: List[str] = []
        n_boxes = len(data.get("text", []))

        for i in range(n_boxes):
            text_str = str(data["text"][i]).strip()
            conf_val = float(data["conf"][i])

            if not text_str or conf_val < 0:
                continue

            conf_normalized = min(1.0, max(0.0, conf_val / 100.0))
            if conf_normalized < effective_config.confidence_threshold:
                continue

            full_text_parts.append(text_str)

            x = float(data["left"][i])
            y = float(data["top"][i])
            w = float(data["width"][i])
            h = float(data["height"][i])

            norm_l = max(0.0, min(1.0, x / width))
            norm_t = max(0.0, min(1.0, y / height))
            norm_r = max(0.0, min(1.0, (x + w) / width))
            norm_b = max(0.0, min(1.0, (y + h) / height))

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
                    confidence=round(conf_normalized, 4),
                    region_idx=len(regions),
                )
            )

        full_text = " ".join(full_text_parts)

        return OCRResult(
            full_text=full_text,
            regions=regions,
            provider_id=self.provider_id,
            model_id=self.model_id,
            image_width=width,
            image_height=height,
            processing_time_ms=round(elapsed_ms, 2),
        )

    def _load_image(
        self, image_input: Union[str, Path, bytes, bytearray, BinaryIO]
    ) -> tuple[bytes, int, int]:
        """Load image bytes and read dimensions."""
        try:
            if isinstance(image_input, (str, Path)):
                p = Path(image_input)
                if not p.exists():
                    raise InvalidImageError(f"Image file not found: {image_input}")
                img_bytes = p.read_bytes()
            elif isinstance(image_input, (bytes, bytearray)):
                img_bytes = bytes(image_input)
            elif hasattr(image_input, "read"):
                img_bytes = image_input.read()
            else:
                raise InvalidImageError(f"Unsupported image input type: {type(image_input)}")

            if len(img_bytes) == 0:
                raise InvalidImageError("Input image source is 0 bytes")

            with Image.open(io.BytesIO(img_bytes)) as img:
                width, height = img.size
                if img.format and img.format.upper() not in (
                    "PNG", "JPEG", "JPG", "WEBP", "TIFF", "TIF", "BMP"
                ):
                    raise UnsupportedImageFormatError(f"Unsupported image format: {img.format}")

            return img_bytes, width, height
        except (InvalidImageError, UnsupportedImageFormatError):
            raise
        except Exception as e:
            raise InvalidImageError(f"Failed to decode image for Tesseract: {e}") from e
