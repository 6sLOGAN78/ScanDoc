"""
Central Model Registry maintaining specifications, availability, and lifecycle states.
"""

import logging
from typing import Dict, List, Optional

from scandoc.models_mgmt.exceptions import ModelNotFoundError
from scandoc.models_mgmt.models import ModelSpec
from scandoc.models_mgmt.taxonomy import ModelFormat, ModelSource, ModelState, TaskType

logger = logging.getLogger("scandoc.models_mgmt.registry")


class ModelRegistry:
    """
    Registry managing known and installed model specifications.
    Decoupled from inference providers.
    """

    def __init__(self, register_defaults: bool = True):
        self._models: Dict[str, ModelSpec] = {}
        if register_defaults:
            self._register_default_specs()

    def _register_default_specs(self) -> None:
        defaults = [
            ModelSpec(
                model_id="rapidocr_onnx",
                provider="rapidocr",
                model_name="RapidOCR Mobile PP-OCRv4 ONNX",
                architecture="PP-OCRv4",
                task=TaskType.OCR,
                format=ModelFormat.ONNX,
                source=ModelSource.URL,
                url="https://github.com/RapidAI/RapidOCR/releases/download/v1.1.0/ch_PP-OCRv4_rec_infer.onnx",
                filename="ch_PP-OCRv4_rec_infer.onnx",
                size_bytes=10857312,
                checksum_sha256="4d7b7e05f6bf79e19d71c4c8d5d9a0937a0753ffc5bc91238612140d344d5c90",
                supported_devices=["cpu", "cuda"],
                supported_runtimes=["onnxruntime"],
                license="Apache-2.0",
                state=ModelState.READY,
            ),
            ModelSpec(
                model_id="rtdetr_doclaynet",
                provider="rtdetr_layout",
                model_name="RT-DETR DocLayNet Layout Analyzer",
                architecture="RT-DETR",
                task=TaskType.LAYOUT,
                format=ModelFormat.ONNX,
                source=ModelSource.URL,
                url="https://huggingface.co/scandoc/rtdetr-doclaynet/resolve/main/rtdetr_doclaynet.onnx",
                filename="rtdetr_doclaynet.onnx",
                size_bytes=44281920,
                checksum_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                supported_devices=["cpu", "cuda", "openvino"],
                supported_runtimes=["onnxruntime"],
                license="Apache-2.0",
                state=ModelState.READY,
            ),
            ModelSpec(
                model_id="slanet_table",
                provider="slanet_table",
                model_name="SLANet Table Structure Recognizer",
                architecture="SLANet",
                task=TaskType.TABLE,
                format=ModelFormat.ONNX,
                source=ModelSource.URL,
                url="https://huggingface.co/scandoc/slanet-table/resolve/main/slanet_table.onnx",
                filename="slanet_table.onnx",
                size_bytes=18492000,
                checksum_sha256="a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
                supported_devices=["cpu", "cuda"],
                supported_runtimes=["onnxruntime"],
                license="Apache-2.0",
                state=ModelState.READY,
            ),
            ModelSpec(
                model_id="basic_figure_analyzer",
                provider="local_figure_analyzer",
                model_name="Basic Figure Analyzer",
                architecture="BasicVision",
                task=TaskType.FIGURE,
                format=ModelFormat.ONNX,
                source=ModelSource.LOCAL_PATH,
                supported_devices=["cpu"],
                state=ModelState.READY,
            ),
            ModelSpec(
                model_id="basic_formula_recognizer",
                provider="local_formula_recognizer",
                model_name="Basic Formula Recognizer",
                architecture="TeXify",
                task=TaskType.FORMULA,
                format=ModelFormat.ONNX,
                source=ModelSource.LOCAL_PATH,
                supported_devices=["cpu"],
                state=ModelState.READY,
            ),
            ModelSpec(
                model_id="pix2text_formula",
                provider="local_formula_recognizer",
                model_name="Pix2Text LaTeX Formula Vision Model",
                architecture="LaTeX-OCR",
                task=TaskType.FORMULA,
                format=ModelFormat.ONNX,
                source=ModelSource.URL,
                url="https://huggingface.co/scandoc/pix2text-formula/resolve/main/latex_ocr.onnx",
                filename="latex_ocr.onnx",
                size_bytes=18920112,
                checksum_sha256="b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b",
                supported_devices=["cpu", "cuda"],
                supported_runtimes=["onnxruntime"],
                license="Apache-2.0",
                state=ModelState.READY,
            ),
            ModelSpec(
                model_id="smolvlm_local",
                provider="local_vlm_engine",
                model_name="SmolVLM Multimodal Vision-Language Model",
                architecture="SmolVLM",
                task=TaskType.VLM,
                format=ModelFormat.SAFETENSORS,
                source=ModelSource.HUGGINGFACE,
                url="HuggingFaceTB/SmolVLM-250M-Instruct",
                filename="model.safetensors",
                size_bytes=512000000,
                checksum_sha256="c8932fa5a7e682d3e9140f7b0e1b2123f8b030e201b1c201490bf706321fa123",
                supported_devices=["cpu", "cuda"],
                supported_runtimes=["torch", "transformers"],
                license="Apache-2.0",
                state=ModelState.READY,
            ),
        ]
        for m in defaults:
            self.register(m)

    def register(self, spec: ModelSpec) -> None:
        """Register or update a model specification in the registry."""
        mid = spec.model_id.lower()
        if mid in self._models:
            logger.debug("Updating registered model specification '%s'", mid)
        self._models[mid] = spec

    def unregister(self, model_id: str) -> Optional[ModelSpec]:
        """Unregister a model specification by ID."""
        mid = model_id.lower()
        return self._models.pop(mid, None)

    def lookup(self, model_id: str) -> Optional[ModelSpec]:
        """Lookup model specification by ID."""
        mid = model_id.lower()
        return self._models.get(mid)

    def list_models(self, task: Optional[TaskType] = None) -> List[ModelSpec]:
        """List registered model specifications, optionally filtered by task type."""
        if task is None:
            return list(self._models.values())
        return [m for m in self._models.values() if m.task == task]

    def update_state(self, model_id: str, state: ModelState) -> None:
        """Update lifecycle state of a registered model."""
        spec = self.lookup(model_id)
        if not spec:
            raise ModelNotFoundError(f"Cannot update state: Model '{model_id}' is not registered.")
        updated = spec.model_copy(update={"state": state})
        self.register(updated)


# Global Singleton
default_model_registry = ModelRegistry()
