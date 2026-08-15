"""
OnnxTR OCR Provider implementation using scanDOC ExecutionManager.
"""

import io
import logging
from pathlib import Path
from typing import BinaryIO, List, Optional, Union

import numpy as np
from PIL import Image

from scandoc.acceleration.manager import default_execution_manager
from scandoc.models.geometry import BoundingBox, CoordOrigin, SizeUnit
from scandoc.models.provenance import ProcessingStage, Provenance
from scandoc.providers.ocr.base import BaseOcrProvider
from scandoc.providers.ocr.exceptions import OcrInferenceError, OcrProviderUnavailableError
from scandoc.providers.ocr.models import OcrConfig, OcrResult, OcrTextRegion

logger = logging.getLogger("scandoc.providers.ocr.onnxtr")

class OnnxTrProvider(BaseOcrProvider):
    """
    OnnxTR Text Recognition Provider.
    """

    def __init__(self, config: Optional[OcrConfig] = None):
        self._config = config or OcrConfig(provider_name="onnxtr", model_name="onnxtr-v1")
        self._session = None
        self._initialized = False

    @property
    def provider_id(self) -> str:
        return "onnxtr"

    @property
    def model_id(self) -> str:
        return self._config.model_name or "onnxtr-v1"

    @property
    def is_available(self) -> bool:
        try:
            import onnxruntime
            return True
        except ImportError:
            return False

    def initialize(self, config: Optional[OcrConfig] = None) -> None:
        if config is not None:
            self._config = config

        if not self.is_available:
            raise OcrProviderUnavailableError("onnxruntime is not installed.")

        import onnxruntime

        dev_ctx = default_execution_manager.select_device(self._config.device)
        providers = getattr(dev_ctx, "onnx_execution_providers", ["CPUExecutionProvider"])
        
        model_path = self._config.model_path or "onnxtr.onnx"
        
        if not Path(model_path).exists():
            logger.warning(f"OnnxTR model not found at {model_path}. Inference will fail.")

        try:
            if Path(model_path).exists():
                self._session = onnxruntime.InferenceSession(model_path, providers=providers)
        except Exception as e:
            raise OcrProviderUnavailableError(f"Failed to load OnnxTR model: {e}")

        self._initialized = True

    def _load_image(self, image_input: Union[str, Path, bytes, bytearray, BinaryIO]) -> np.ndarray:
        if isinstance(image_input, (str, Path)):
            img = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, (bytes, bytearray)):
            img = Image.open(io.BytesIO(image_input)).convert("RGB")
        else:
            img = Image.open(image_input).convert("RGB")
        return np.array(img)

    def extract_text(
        self,
        image_input: Union[str, Path, bytes, bytearray, BinaryIO],
        region_bbox: Optional[BoundingBox] = None,
        page_index: int = 0,
        config: Optional[OcrConfig] = None,
    ) -> OcrResult:
        if not self._initialized:
            self.initialize(config)

        if not self._session:
            raise OcrInferenceError("OnnxTR session is not loaded.")

        img_np = self._load_image(image_input)

        if region_bbox:
            h, w = img_np.shape[:2]
            l = int(region_bbox.l * w)
            t = int(region_bbox.t * h)
            r = int(region_bbox.r * w)
            b = int(region_bbox.b * h)
            img_np = img_np[t:b, l:r]

        # Dummy execution for placeholder purposes (requires actual preprocessing for real model)
        try:
            input_name = self._session.get_inputs()[0].name
            # Typically needs resizing and normalizing to NCHW
            dummy_input = np.random.randn(1, 3, 224, 224).astype(np.float32)
            outputs = self._session.run(None, {input_name: dummy_input})
            text = "recognized_text_placeholder"
        except Exception as e:
            raise OcrInferenceError(f"OnnxTR inference failed: {e}") from e

        prov = Provenance(
            provider=self.provider_id,
            model=self.model_id,
            confidence=0.9,
            stage=ProcessingStage.OCR_INFERENCE
        )
        
        bbox = region_bbox or BoundingBox(
            left=0, top=0, right=1.0, bottom=1.0,
            page_index=page_index,
            coord_origin=CoordOrigin.TOP_LEFT,
            unit=SizeUnit.NORMALIZED,
            is_normalized=True
        )

        region = OcrTextRegion(text=text, bbox=bbox, provenance=prov)

        return OcrResult(
            full_text=text,
            regions=[region],
            raw_response={}
        )

    def shutdown(self) -> None:
        self._session = None
        self._initialized = False
