"""
EasyOCR Provider implementation using PyTorch and scanDOC ExecutionManager.
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

logger = logging.getLogger("scandoc.providers.ocr.easyocr")

class EasyOcrProvider(BaseOcrProvider):
    """
    EasyOCR Text Recognition Provider.
    """

    def __init__(self, config: Optional[OcrConfig] = None):
        self._config = config or OcrConfig(provider_name="easyocr", model_name="easyocr-en")
        self._reader = None
        self._initialized = False

    @property
    def provider_id(self) -> str:
        return "easyocr"

    @property
    def model_id(self) -> str:
        return self._config.model_name or "easyocr-en"

    @property
    def is_available(self) -> bool:
        try:
            import easyocr
            return True
        except ImportError:
            return False

    def initialize(self, config: Optional[OcrConfig] = None) -> None:
        if config is not None:
            self._config = config

        if not self.is_available:
            raise OcrProviderUnavailableError("easyocr is not installed.")

        import easyocr

        # Use execution manager for device selection
        dev_ctx = default_execution_manager.select_device(self._config.device)
        gpu = dev_ctx.device_type.value == "cuda"

        lang_list = self._config.languages if self._config.languages else ["en"]
        self._reader = easyocr.Reader(lang_list, gpu=gpu)
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

        img_np = self._load_image(image_input)
        h, w = img_np.shape[:2]

        if region_bbox:
            l = int(region_bbox.l * w)
            t = int(region_bbox.t * h)
            r = int(region_bbox.r * w)
            b = int(region_bbox.b * h)
            img_np = img_np[t:b, l:r]

        try:
            results = self._reader.readtext(img_np)
        except Exception as e:
            raise OcrInferenceError(f"EasyOCR inference failed: {e}") from e

        regions = []
        full_text = []

        for res in results:
            box, text, prob = res
            tl, tr, br, bl = box
            
            # Normalize to parent crop coordinates
            ch, cw = img_np.shape[:2]
            l = min(tl[0], bl[0]) / cw
            t = min(tl[1], tr[1]) / ch
            r = max(tr[0], br[0]) / cw
            b = max(bl[1], br[1]) / ch

            bbox = BoundingBox(
                left=round(l, 5),
                top=round(t, 5),
                right=round(r, 5),
                bottom=round(b, 5),
                page_index=page_index,
                coord_origin=CoordOrigin.TOP_LEFT,
                unit=SizeUnit.NORMALIZED,
                is_normalized=True
            )

            prov = Provenance(
                provider=self.provider_id,
                model=self.model_id,
                confidence=float(prob),
                stage=ProcessingStage.OCR_INFERENCE
            )

            regions.append(OcrTextRegion(text=text, bbox=bbox, provenance=prov))
            full_text.append(text)

        return OcrResult(
            full_text="\\n".join(full_text),
            regions=regions,
            raw_response={"easyocr_results": len(results)}
        )

    def shutdown(self) -> None:
        self._reader = None
        self._initialized = False

