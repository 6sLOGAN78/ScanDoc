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
                model_id="easyocr",
                provider="easyocr_engine",
                model_name="EasyOCR (Accurate)",
                architecture="CRNN",
                task=TaskType.OCR,
                format=ModelFormat.ONNX,
                source=ModelSource.URL,
                url="https://github.com/JaidedAI/EasyOCR/releases/download/v1.6.1/easyocr.zip",
                filename="easyocr.onnx",
                size_bytes=85000000,
                supported_devices=["cpu", "cuda"],
                state=ModelState.READY,
            ),
            ModelSpec(
                model_id="tesseract",
                provider="tesseract_engine",
                model_name="Tesseract OCR (Legacy)",
                architecture="LSTM",
                task=TaskType.OCR,
                format=ModelFormat.ONNX,
                source=ModelSource.URL,
                url="https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata",
                filename="eng.traineddata",
                size_bytes=30000000,
                supported_devices=["cpu"],
                state=ModelState.READY,
            ),
            ModelSpec(
                model_id="onnxtr",
                provider="onnxtr_engine",
                model_name="OnnxTR (Transformer OCR)",
                architecture="Transformer",
                task=TaskType.OCR,
                format=ModelFormat.ONNX,
                source=ModelSource.URL,
                url="https://huggingface.co/scandoc/onnxtr/resolve/main/onnxtr.onnx",
                filename="onnxtr.onnx",
                size_bytes=210000000,
                supported_devices=["cpu", "cuda"],
                state=ModelState.READY,
            ),
            ModelSpec(
                model_id="nemotron_ocr",
                provider="nemotron_engine",
                model_name="NVIDIA Nemotron-OCR (Heavy)",
                architecture="Nemotron",
                task=TaskType.OCR,
                format=ModelFormat.ONNX,
                source=ModelSource.URL,
                url="https://huggingface.co/nvidia/nemotron-ocr/resolve/main/nemotron.onnx",
                filename="nemotron.onnx",
                size_bytes=4500000000,
                supported_devices=["cpu", "cuda"],
                state=ModelState.READY,
            ),
            ModelSpec(
                model_id="docling_heron",
                provider="docling_engine",
                model_name="Docling Heron Layout (Heavy)",
                architecture="Heron",
                task=TaskType.LAYOUT,
                format=ModelFormat.ONNX,
                source=ModelSource.URL,
                url="https://huggingface.co/docling/heron/resolve/main/heron.onnx",
                filename="heron.onnx",
                size_bytes=1200000000,
                supported_devices=["cpu", "cuda"],
                state=ModelState.READY,
            ),
            ModelSpec(
                model_id="tableformerv2",
                provider="tableformer_engine",
                model_name="TableFormerV2 (Transformer)",
                architecture="TableFormer",
                task=TaskType.TABLE,
                format=ModelFormat.ONNX,
                source=ModelSource.URL,
                url="https://huggingface.co/scandoc/tableformerv2/resolve/main/tableformerv2.onnx",
                filename="tableformerv2.onnx",
                size_bytes=340000000,
                supported_devices=["cpu", "cuda"],
                state=ModelState.READY,
            ),
            ModelSpec(
                model_id="codeformulav2",
                provider="formula_engine",
                model_name="CodeFormulaV2 (Accurate)",
                architecture="CodeFormula",
                task=TaskType.FORMULA,
                format=ModelFormat.ONNX,
                source=ModelSource.URL,
                url="https://huggingface.co/scandoc/codeformulav2/resolve/main/codeformulav2.onnx",
                filename="codeformulav2.onnx",
                size_bytes=110000000,
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
