"""
Pix2Text Formula Provider implementation using PyTorch and scanDOC ExecutionManager.
"""

import io
import logging
from pathlib import Path
from typing import BinaryIO, List, Optional, Union

from PIL import Image

from scandoc.acceleration.manager import default_execution_manager
from scandoc.models.geometry import BoundingBox
from scandoc.providers.formulas.base import BaseFormulaProvider
from scandoc.providers.formulas.exceptions import FormulaInferenceError, FormulaProviderUnavailableError
from scandoc.providers.formulas.models import FormulaConfig, FormulaResult

logger = logging.getLogger("scandoc.providers.formulas.pix2text")

class Pix2TextProvider(BaseFormulaProvider):
    """
    Pix2Text Formula Recognition Provider.
    """

    def __init__(self, config: Optional[FormulaConfig] = None):
        self._config = config or FormulaConfig(provider_name="pix2text", model_name="pix2text-mfd")
        self._p2t = None
        self._initialized = False

    @property
    def provider_id(self) -> str:
        return "pix2text"

    @property
    def model_id(self) -> str:
        return self._config.model_name or "pix2text-mfd"

    @property
    def is_available(self) -> bool:
        try:
            import pix2text
            return True
        except ImportError:
            return False

    def initialize(self, config: Optional[FormulaConfig] = None) -> None:
        if config is not None:
            self._config = config

        if not self.is_available:
            raise FormulaProviderUnavailableError("pix2text is not installed.")

        from pix2text import Pix2Text

        dev_ctx = default_execution_manager.select_device(getattr(self._config, 'device', 'auto'))
        device = "cuda" if dev_ctx.device_type.value == "cuda" else "cpu"

        try:
            self._p2t = Pix2Text.from_config(device=device)
        except Exception as e:
            raise FormulaProviderUnavailableError(f"Failed to load Pix2Text: {e}")

        self._initialized = True

    def _load_image(self, image_input: Union[str, Path, bytes, bytearray, BinaryIO]) -> Image.Image:
        if isinstance(image_input, (str, Path)):
            return Image.open(image_input).convert("RGB")
        elif isinstance(image_input, (bytes, bytearray)):
            return Image.open(io.BytesIO(image_input)).convert("RGB")
        return Image.open(image_input).convert("RGB")

    def extract_formula(
        self,
        image_input: Union[str, Path, bytes, bytearray, BinaryIO],
        region_bbox: Optional[BoundingBox] = None,
        page_index: int = 0,
        config: Optional[FormulaConfig] = None,
    ) -> FormulaResult:
        if not self._initialized:
            self.initialize(config)

        img = self._load_image(image_input)
        
        if region_bbox:
            l = int(region_bbox.l * img.width)
            t = int(region_bbox.t * img.height)
            r = int(region_bbox.r * img.width)
            b = int(region_bbox.b * img.height)
            img = img.crop((l, t, r, b))

        try:
            # P2T recognizes formulas
            result = self._p2t.recognize_formula(img)
            latex_text = result if isinstance(result, str) else str(result)
        except Exception as e:
            raise FormulaInferenceError(f"Pix2Text inference failed: {e}") from e

        return FormulaResult(
            latex=latex_text,
            provider="pix2text",
            confidence=0.9
        )

    def shutdown(self) -> None:
        self._p2t = None
        self._initialized = False
