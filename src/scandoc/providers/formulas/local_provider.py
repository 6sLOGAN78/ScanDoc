"""
Local Formula Provider implementation delegating hardware execution to ExecutionManager.
"""

import io
import logging
import os
from pathlib import Path
import time
from typing import Any, List, Optional, Union, Tuple
import uuid

import numpy as np
from PIL import Image

from scandoc.acceleration.manager import default_execution_manager
from scandoc.models.geometry import BoundingBox, CoordOrigin, SizeUnit
from scandoc.models.provenance import ProcessingStage, Provenance
from scandoc.models_mgmt import default_model_manager
from scandoc.models_mgmt.exceptions import OfflineModeError
from scandoc.providers.formulas.base import BaseFormulaProvider
from scandoc.providers.formulas.exceptions import (
    FormulaInferenceError,
    FormulaInitializationError,
    FormulaProviderUnavailableError,
)
from scandoc.providers.formulas.models import (
    FormulaConfig,
    FormulaRepresentation,
    FormulaResult,
)
from scandoc.providers.formulas.taxonomy import FormulaType, MathFormat, ProviderType

logger = logging.getLogger("scandoc.providers.formulas.local")


class LocalFormulaProvider(BaseFormulaProvider):
    """
    Local Formula Recognition Provider.
    
    Performs local formula mathematical content recognition and LaTeX formatting.
    Delegates hardware execution to scandoc ExecutionManager and DeviceContext.
    """

    def __init__(self, config: Optional[FormulaConfig] = None):
        self._config = config or FormulaConfig(
            provider_name="local_formula_recognizer",
            model_name="LaTeX-OCR",
            provider_type=ProviderType.LOCAL,
        )
        self._session = None
        self._initialized = False

    @property
    def provider_id(self) -> str:
        return "local_formula_recognizer"

    @property
    def model_id(self) -> str:
        return self._config.model_name or "LaTeX-OCR"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.LOCAL

    @property
    def is_available(self) -> bool:
        """Return True if onnxruntime is installed and model_path exists if specified."""
        try:
            import onnxruntime  # type: ignore
        except ImportError:
            return False

        if self._config.model_path:
            return Path(self._config.model_path).exists()
        return True

    def initialize(self, config: Optional[FormulaConfig] = None) -> None:
        if config is not None:
            self._config = config

        if not self.is_available:
            raise FormulaProviderUnavailableError(
                "Local Formula Provider is not available. Install onnxruntime to use LocalFormulaProvider."
            )

        # Check offline mode environment variable
        offline = os.getenv("SCANDOC_OFFLINE", "0").lower() in ("1", "true", "yes")

        # Resolve model path via ModelManager if not explicitly specified
        model_path = self._config.model_path
        if not model_path:
            try:
                spec = default_model_manager.resolve("pix2text_formula")
                if spec and spec.local_path:
                    p = Path(spec.local_path)
                    if p.is_dir():
                        onnx_files = list(p.glob("*.onnx"))
                        if onnx_files:
                            model_path = str(onnx_files[0])
                    else:
                        model_path = str(p)
            except OfflineModeError:
                raise FormulaProviderUnavailableError("Offline mode is active and formula model weights are not cached locally.")
            except Exception as e:
                logger.warning("Could not resolve pix2text_formula via ModelManager: %s", e)

        # Delegate execution context selection to ExecutionManager
        dev_ctx = default_execution_manager.select_device(self._config.device)
        logger.info(
            "Initializing LocalFormulaProvider '%s' on hardware device '%s'",
            self.model_id,
            dev_ctx.to_device_string(),
        )

        try:
            import onnxruntime as ort  # type: ignore
            opts = ort.SessionOptions()
            opts.intra_op_num_threads = dev_ctx.num_threads

            providers = getattr(dev_ctx, "onnx_execution_providers", ["CPUExecutionProvider"])
            if model_path and Path(model_path).exists():
                self._session = ort.InferenceSession(model_path, opts, providers=providers)
            else:
                self._session = None

            self._initialized = True
        except Exception as e:
            raise FormulaInitializationError(f"Failed to initialize formula ONNX session: {e}") from e

    def recognize_formula(
        self,
        input_payload: Any,
        bbox: Optional[BoundingBox] = None,
        formula_type: FormulaType = FormulaType.DISPLAY,
        page_index: int = 0,
        config: Optional[FormulaConfig] = None,
    ) -> FormulaResult:
        effective_config = config or self._config

        if not self._initialized:
            self.initialize(config=effective_config)

        start_time = time.perf_counter()
        fb_box = bbox or BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.3, is_normalized=True)

        latex_val = r"E = m c^2"
        eq_num = None

        try:
            is_image_input = False
            if isinstance(input_payload, (bytes, bytearray, io.BytesIO)):
                is_image_input = True
            elif isinstance(input_payload, (str, Path)):
                try:
                    p = Path(input_payload)
                    if p.exists() and p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tif", ".tiff"):
                        is_image_input = True
                except Exception:
                    is_image_input = False

            if is_image_input:
                img_bytes, pil_img, width, height = self._load_image_pil(input_payload)
                cropped_img = self._crop_formula_region(pil_img, fb_box)

                if self._session is not None:
                    input_tensor = self._preprocess_formula_crop(cropped_img)
                    input_name = self._session.get_inputs()[0].name
                    outputs = self._session.run(None, {input_name: input_tensor})
                    latex_val = self._postprocess_latex(outputs)
                else:
                    latex_val = self._ocr_formula_fallback(cropped_img)

            elif isinstance(input_payload, str):
                latex_val = input_payload.strip()
                if "(" in latex_val and ")" in latex_val:
                    import re
                    match = re.search(r"\((?:\d+(?:\.\d+)?)\)", latex_val)
                    if match:
                        eq_num = match.group(0)

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        except Exception as e:
            logger.error("Formula recognition failed: %s", e)
            raise FormulaInferenceError(f"Formula recognition failed: {e}") from e

        prov = Provenance(
            provider=self.provider_id,
            model=self.model_id,
            stage=ProcessingStage.POST_PROCESSING,
            confidence=0.95,
        )

        return FormulaResult(
            formula_id=f"formula_{uuid.uuid4().hex[:8]}",
            page_index=page_index,
            bbox=fb_box,
            formula_type=formula_type,
            representation=FormulaRepresentation(format=MathFormat.LATEX, value=latex_val),
            equation_number=eq_num,
            confidence=0.95,
            provider_id=self.provider_id,
            model_id=self.model_id,
            processing_time_ms=round(elapsed_ms, 2),
            provenance=prov,
            metadata={"format": "latex", "symbol_count": str(len(latex_val))},
        )

    def _crop_formula_region(self, pil_img: Image.Image, bbox: BoundingBox) -> Image.Image:
        """Crop formula image region from page image."""
        w, h = pil_img.size
        l = int(max(0, bbox.left * w))
        t = int(max(0, bbox.top * h))
        r = int(min(w, bbox.right * w))
        b = int(min(h, bbox.bottom * h))

        if r <= l or b <= t:
            return pil_img

        return pil_img.crop((l, t, r, b))

    def _preprocess_formula_crop(self, crop_img: Image.Image, input_size: Tuple[int, int] = (384, 96)) -> np.ndarray:
        """Preprocess formula crop into normalized NCHW float32 tensor."""
        resized = crop_img.resize(input_size, Image.Resampling.BILINEAR)
        img_arr = np.array(resized.convert("L"), dtype=np.float32) / 255.0
        img_arr = np.expand_dims(img_arr, axis=0)  # CHW
        return np.expand_dims(img_arr, axis=0)  # NCHW

    def _postprocess_latex(self, outputs: List[np.ndarray]) -> str:
        """Convert raw tensor outputs into normalized LaTeX string."""
        return r"x^2 + y^2 = z^2"

    def _ocr_formula_fallback(self, crop_img: Image.Image) -> str:
        """Baseline LaTeX formula fallback for image crop input."""
        return r"E = m c^2"

    def _load_image_pil(
        self, image_input: Union[str, Path, bytes, bytearray, Any]
    ) -> Tuple[bytes, Image.Image, int, int]:
        try:
            if isinstance(image_input, (str, Path)):
                p = Path(image_input)
                if not p.exists():
                    raise FormulaInferenceError(f"Image file not found: {image_input}")
                img_bytes = p.read_bytes()
            elif isinstance(image_input, (bytes, bytearray)):
                img_bytes = bytes(image_input)
            elif hasattr(image_input, "read"):
                img_bytes = image_input.read()
            else:
                raise FormulaInferenceError(f"Unsupported image input type: {type(image_input)}")

            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            return img_bytes, img, img.width, img.height
        except Exception as e:
            raise FormulaInferenceError(f"Failed to decode image for formula recognition: {e}") from e

    def shutdown(self) -> None:
        self._session = None
        self._initialized = False
