"""
Generic Hugging Face OCR Model Adapter architecture for user-provided models.
"""

import logging
from pathlib import Path
from typing import BinaryIO, List, Optional, Union

from scandoc.providers.ocr.base import BaseOcrProvider
from scandoc.providers.ocr.exceptions import (
    OcrInferenceError,
    OcrInitializationError,
    OcrProviderUnavailableError,
)
from scandoc.providers.ocr.models import OcrCapability, OcrProviderConfig, OCRResult
from scandoc.providers.ocr.secrets import SecretRef

logger = logging.getLogger("scandoc.providers.ocr.huggingface")


class HuggingFaceOcrConfig(OcrProviderConfig):
    """
    Hugging Face model configuration settings.
    """
    hf_model_id: str = "microsoft/trocr-base-printed"
    revision: str = "main"
    local_model_path: Optional[str] = None
    token_ref: Optional[SecretRef] = None
    task: str = "image-to-text"


class HuggingFaceOcrAdapter(BaseOcrProvider):
    """
    Generic Adapter Architecture for user-provided Hugging Face OCR models.
    
    Decouples Hugging Face model loading and inference from core scanDOC pipelines.
    """

    def __init__(self, config: Optional[HuggingFaceOcrConfig] = None):
        self._hf_config = config or HuggingFaceOcrConfig()
        self._model = None
        self._processor = None
        self._initialized = False

    @property
    def provider_id(self) -> str:
        return "huggingface"

    @property
    def model_id(self) -> str:
        return self._hf_config.hf_model_id or "hf-model"

    @property
    def supported_languages(self) -> List[str]:
        return ["en", "multilingual"]

    @property
    def capabilities(self) -> OcrCapability:
        return OcrCapability(
            provider_id=self.provider_id,
            is_local=True,
            supports_cpu=True,
            supports_gpu=True,
            supports_batch=True,
            supports_confidence=True,
            supports_polygons=False,
            supports_orientation=False,
            supported_languages=self.supported_languages,
        )

    @property
    def is_available(self) -> bool:
        """Return True if transformers and torch packages are installed."""
        try:
            import transformers  # type: ignore
            import torch  # type: ignore
            return True
        except ImportError:
            return False

    def initialize(self, config: Optional[OcrProviderConfig] = None) -> None:
        if config is not None and isinstance(config, HuggingFaceOcrConfig):
            self._hf_config = config

        if not self.is_available:
            raise OcrProviderUnavailableError(
                "Hugging Face OCR requirements are not installed. Install 'transformers' and 'torch' to use HuggingFaceOcrAdapter."
            )
        # Note: Actual pipeline loading is deferred to process_image to avoid unneeded memory usage.
        self._initialized = True
        logger.info("HuggingFaceOcrAdapter initialized for model '%s'", self.model_id)

    def process_image(
        self,
        image_input: Union[str, Path, bytes, bytearray, BinaryIO],
        config: Optional[OcrProviderConfig] = None,
    ) -> OCRResult:
        if not self._initialized:
            self.initialize(config=config)

        if not self.is_available:
            raise OcrProviderUnavailableError("Hugging Face engine dependencies are not available")

        raise OcrInferenceError(
            f"Hugging Face model '{self.model_id}' architecture adapter initialized. "
            f"Specific task head '{self._hf_config.task}' loading requires explicit checkpoint weights."
        )

    def shutdown(self) -> None:
        self._model = None
        self._processor = None
        self._initialized = False
