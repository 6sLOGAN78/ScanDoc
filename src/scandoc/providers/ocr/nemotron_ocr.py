"""
Nemotron-OCR Provider implementation using PyTorch and scanDOC ExecutionManager.
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

logger = logging.getLogger("scandoc.providers.ocr.nemotron")

class NemotronOcrProvider(BaseOcrProvider):
    """
    Nemotron-OCR Text Recognition Provider.
    """

    def __init__(self, config: Optional[OcrConfig] = None):
        self._config = config or OcrConfig(provider_name="nemotron_ocr", model_name="nvidia/nemotron-ocr")
        self._model = None
        self._processor = None
        self._initialized = False

    @property
    def provider_id(self) -> str:
        return "nemotron_ocr"

    @property
    def model_id(self) -> str:
        return self._config.model_name or "nvidia/nemotron-ocr"

    @property
    def is_available(self) -> bool:
        try:
            import torch
            import transformers
            return True
        except ImportError:
            return False

    def initialize(self, config: Optional[OcrConfig] = None) -> None:
        if config is not None:
            self._config = config

        if not self.is_available:
            raise OcrProviderUnavailableError("torch and transformers are not installed.")

        import torch
        from transformers import AutoProcessor, AutoModelForVision2Seq

        dev_ctx = default_execution_manager.select_device(self._config.device)
        self.device = torch.device("cuda" if dev_ctx.device_type.value == "cuda" else "cpu")
        dtype = torch.float16 if self.device.type == "cuda" else torch.float32

        try:
            self._processor = AutoProcessor.from_pretrained(self.model_id)
            self._model = AutoModelForVision2Seq.from_pretrained(
                self.model_id, 
                torch_dtype=dtype
            ).to(self.device)
            self._model.eval()
        except Exception as e:
            raise OcrProviderUnavailableError(f"Failed to load Nemotron-OCR: {e}")

        self._initialized = True

    def _load_image(self, image_input: Union[str, Path, bytes, bytearray, BinaryIO]) -> Image.Image:
        if isinstance(image_input, (str, Path)):
            return Image.open(image_input).convert("RGB")
        elif isinstance(image_input, (bytes, bytearray)):
            return Image.open(io.BytesIO(image_input)).convert("RGB")
        return Image.open(image_input).convert("RGB")

    def extract_text(
        self,
        image_input: Union[str, Path, bytes, bytearray, BinaryIO],
        region_bbox: Optional[BoundingBox] = None,
        page_index: int = 0,
        config: Optional[OcrConfig] = None,
    ) -> OcrResult:
        if not self._initialized:
            self.initialize(config)

        img = self._load_image(image_input)

        if region_bbox:
            l = int(region_bbox.l * img.width)
            t = int(region_bbox.t * img.height)
            r = int(region_bbox.r * img.width)
            b = int(region_bbox.b * img.height)
            img = img.crop((l, t, r, b))

        import torch
        inputs = self._processor(images=img, return_tensors="pt").to(self.device, dtype=self._model.dtype)
        
        try:
            with torch.no_grad():
                outputs = self._model.generate(**inputs, max_new_tokens=512)
                
            text = self._processor.batch_decode(outputs, skip_special_tokens=True)[0]
        except Exception as e:
            raise OcrInferenceError(f"Nemotron-OCR inference failed: {e}") from e

        prov = Provenance(
            provider=self.provider_id,
            model=self.model_id,
            confidence=0.95,
            stage=ProcessingStage.OCR_INFERENCE
        )
        
        bbox = region_bbox or BoundingBox(
            left=0, top=0, right=1.0, bottom=1.0,
            page_index=page_index,
            coord_origin=CoordOrigin.TOP_LEFT,
            unit=SizeUnit.NORMALIZED,
            is_normalized=True
        )

        region = OcrTextRegion(text=text.strip(), bbox=bbox, provenance=prov)

        return OcrResult(
            full_text=text.strip(),
            regions=[region],
            raw_response={}
        )

    def shutdown(self) -> None:
        self._model = None
        self._processor = None
        self._initialized = False
