"""
Generic Remote HTTP OCR Provider and response adapter mechanism.
"""

from abc import ABC, abstractmethod
import io
import json
import logging
from pathlib import Path
import time
from typing import BinaryIO, Dict, List, Optional, Union
import urllib.request
import urllib.error

from PIL import Image

from scandoc.models.geometry import BoundingBox, CoordOrigin, SizeUnit
from scandoc.providers.ocr.base import BaseOcrProvider
from scandoc.providers.ocr.exceptions import (
    InvalidImageError,
    OcrInferenceError,
    OcrInitializationError,
    OcrProviderUnavailableError,
)
from scandoc.providers.ocr.models import OcrCapability, OcrProviderConfig, OCRResult, OCRTextRegion

logger = logging.getLogger("scandoc.providers.ocr.remote")


class BaseHttpResponseAdapter(ABC):
    """
    Abstract adapter interface converting remote HTTP JSON responses into normalized OCRResult objects.
    """

    @abstractmethod
    def parse_response(
        self,
        json_data: Dict,
        image_width: int,
        image_height: int,
        provider_id: str,
        model_id: str,
        processing_time_ms: float,
    ) -> OCRResult:
        pass


class DefaultHttpResponseAdapter(BaseHttpResponseAdapter):
    """
    Standard JSON response adapter.
    
    Expects JSON structure:
    {
      "full_text": "...",
      "regions": [
        {"text": "Line 1", "bbox": [left, top, right, bottom], "confidence": 0.95}
      ]
    }
    """

    def parse_response(
        self,
        json_data: Dict,
        image_width: int,
        image_height: int,
        provider_id: str,
        model_id: str,
        processing_time_ms: float,
    ) -> OCRResult:
        full_text = json_data.get("full_text") or json_data.get("text") or ""
        raw_regions = json_data.get("regions", [])

        regions: List[OCRTextRegion] = []
        for idx, item in enumerate(raw_regions):
            txt = str(item.get("text", "")).strip()
            conf = float(item.get("confidence", 1.0))
            bbox_raw = item.get("bbox", [0.0, 0.0, 1.0, 1.0])

            bbox = BoundingBox(
                left=float(bbox_raw[0]),
                top=float(bbox_raw[1]),
                right=float(bbox_raw[2]),
                bottom=float(bbox_raw[3]),
                coord_origin=CoordOrigin.TOP_LEFT,
                unit=SizeUnit.NORMALIZED,
                is_normalized=True,
            )

            regions.append(
                OCRTextRegion(
                    text=txt,
                    bbox=bbox,
                    confidence=min(1.0, max(0.0, conf)),
                    region_idx=idx,
                )
            )

        return OCRResult(
            full_text=full_text,
            regions=regions,
            provider_id=provider_id,
            model_id=model_id,
            image_width=image_width,
            image_height=image_height,
            processing_time_ms=processing_time_ms,
        )


class GenericRemoteOcrProvider(BaseOcrProvider):
    """
    Generic Remote HTTP OCR Provider.
    
    Dispatches image processing requests to a configurable remote HTTP/HTTPS OCR endpoint.
    Uses SecretRef for authentication headers, ensuring raw API keys are never leaked.
    """

    def __init__(
        self,
        config: Optional[OcrProviderConfig] = None,
        adapter: Optional[BaseHttpResponseAdapter] = None,
    ):
        self._config = config or OcrProviderConfig(provider_name="remote_http", model_name="generic_remote")
        self._adapter = adapter or DefaultHttpResponseAdapter()
        self._initialized = False

    @property
    def provider_id(self) -> str:
        return self._config.provider_name or "remote_http"

    @property
    def model_id(self) -> str:
        return self._config.model_name or "generic_remote"

    @property
    def supported_languages(self) -> List[str]:
        return ["en", "auto"]

    @property
    def capabilities(self) -> OcrCapability:
        return OcrCapability(
            provider_id=self.provider_id,
            is_local=False,
            supports_cpu=False,
            supports_gpu=True,
            supports_batch=True,
            supports_confidence=True,
            supports_polygons=False,
            supports_orientation=False,
            supported_languages=self.supported_languages,
        )

    @property
    def is_available(self) -> bool:
        return bool(self._config.endpoint)

    def initialize(self, config: Optional[OcrProviderConfig] = None) -> None:
        if config is not None:
            self._config = config

        if not self._config.endpoint:
            raise OcrInitializationError(
                "GenericRemoteOcrProvider requires a valid HTTP endpoint URL in config.endpoint"
            )
        self._initialized = True
        logger.info("GenericRemoteOcrProvider initialized with endpoint '%s'", self._config.endpoint)

    def process_image(
        self,
        image_input: Union[str, Path, bytes, bytearray, BinaryIO],
        config: Optional[OcrProviderConfig] = None,
    ) -> OCRResult:
        if not self._initialized:
            self.initialize(config=config)

        effective_config = config or self._config
        endpoint = effective_config.endpoint

        if not endpoint:
            raise OcrProviderUnavailableError("Remote HTTP OCR endpoint is not configured")

        # Step 1: Read image bytes & dimensions
        img_bytes, width, height = self._load_image(image_input)

        # Step 2: Build HTTP Request Headers (Using SecretRef for Auth)
        headers = {"Content-Type": "application/octet-stream"}
        if effective_config.api_key_ref:
            secret_val = effective_config.api_key_ref.get_secret_value()
            if secret_val:
                headers["Authorization"] = f"Bearer {secret_val}"

        # Step 3: Execute HTTP Request
        start_time = time.perf_counter()
        req = urllib.request.Request(endpoint, data=img_bytes, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=effective_config.timeout_sec) as resp:
                resp_bytes = resp.read()
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                json_data = json.loads(resp_bytes.decode("utf-8"))
        except urllib.error.HTTPError as e:
            # Mask headers and body to avoid secret leakage in exception message
            raise OcrInferenceError(f"Remote OCR HTTP Error status {e.code}") from e
        except Exception as e:
            raise OcrInferenceError(f"Remote OCR network request failed: {e}") from e

        # Step 4: Parse Response via Adapter
        return self._adapter.parse_response(
            json_data=json_data,
            image_width=width,
            image_height=height,
            provider_id=self.provider_id,
            model_id=self.model_id,
            processing_time_ms=round(elapsed_ms, 2),
        )

    def _load_image(
        self, image_input: Union[str, Path, bytes, bytearray, BinaryIO]
    ) -> tuple[bytes, int, int]:
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

            return img_bytes, width, height
        except InvalidImageError:
            raise
        except Exception as e:
            raise InvalidImageError(f"Failed to decode image for remote OCR: {e}") from e
