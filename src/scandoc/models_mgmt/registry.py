"""
Central Model Registry maintaining specifications, availability, and lifecycle states.
"""

import logging
from typing import Dict, List, Optional

from scandoc.models_mgmt.exceptions import ModelNotFoundError
from scandoc.models_mgmt.models import ModelSpec
from scandoc.models_mgmt.taxonomy import ModelState, TaskType

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
                model_name="RapidOCR Mobile ONNX",
                architecture="PP-OCRv4",
                task=TaskType.OCR,
                supported_devices=["cpu", "cuda"],
                state=ModelState.READY,
            ),
            ModelSpec(
                model_id="rtdetr_doclaynet",
                provider="rtdetr_layout",
                model_name="RT-DETR DocLayNet Layout Analyzer",
                architecture="RT-DETR",
                task=TaskType.LAYOUT,
                supported_devices=["cpu", "cuda", "openvino"],
                state=ModelState.READY,
            ),
            ModelSpec(
                model_id="slanet_table",
                provider="slanet_table",
                model_name="SLANet Table Structure Recognizer",
                architecture="SLANet",
                task=TaskType.TABLE,
                supported_devices=["cpu", "cuda"],
                state=ModelState.READY,
            ),
            ModelSpec(
                model_id="basic_figure_analyzer",
                provider="local_figure_analyzer",
                model_name="Basic Figure Analyzer",
                architecture="BasicVision",
                task=TaskType.FIGURE,
                supported_devices=["cpu"],
                state=ModelState.READY,
            ),
            ModelSpec(
                model_id="basic_formula_recognizer",
                provider="local_formula_recognizer",
                model_name="Basic Formula Recognizer",
                architecture="TeXify",
                task=TaskType.FORMULA,
                supported_devices=["cpu"],
                state=ModelState.READY,
            ),
            ModelSpec(
                model_id="pix2text_formula",
                provider="local_formula_recognizer",
                model_name="Pix2Text LaTeX Formula Vision Model",
                architecture="LaTeX-OCR",
                task=TaskType.FORMULA,
                supported_devices=["cpu", "cuda"],
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
