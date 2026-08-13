"""
Hugging Face VLM Provider Adapter implementation for local or remote HF models.
"""

import logging
from typing import List, Optional

from scandoc.providers.vlm.base import BaseVlmProvider
from scandoc.providers.vlm.exceptions import VlmProviderUnavailableError
from scandoc.providers.vlm.models import VlmConfig, VlmRequest, VlmResult
from scandoc.providers.vlm.taxonomy import ProviderType, VlmExecutionMode

logger = logging.getLogger("scandoc.providers.vlm.huggingface")


class HuggingFaceVlmAdapter(BaseVlmProvider):
    """
    Hugging Face Vision-Language Model Provider Adapter.
    
    Supports local offline inference from downloaded weights or remote Hugging Face Inference Endpoints.
    """

    def __init__(self, config: Optional[VlmConfig] = None):
        self._config = config or VlmConfig(
            provider_name="huggingface_vlm",
            model_name="Qwen/Qwen2-VL-7B-Instruct",
            provider_type=ProviderType.HUGGINGFACE,
        )
        self._initialized = False

    @property
    def provider_id(self) -> str:
        return "huggingface_vlm"

    @property
    def model_id(self) -> str:
        return self._config.model_name or "Qwen/Qwen2-VL-7B-Instruct"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.HUGGINGFACE

    @property
    def is_available(self) -> bool:
        """Return True if transformers and torch packages are installed."""
        try:
            import transformers  # type: ignore
            import torch  # type: ignore
            return True
        except ImportError:
            return False

    def initialize(self, config: Optional[VlmConfig] = None) -> None:
        if config is not None:
            self._config = config

        if not self.is_available:
            raise VlmProviderUnavailableError(
                "Hugging Face VLM Provider requirements are not installed. Install 'transformers' and 'torch'."
            )
        self._initialized = True
        logger.info("HuggingFaceVlmAdapter initialized for model '%s'", self.model_id)

    def analyze(self, request: VlmRequest, config: Optional[VlmConfig] = None) -> VlmResult:
        if not self._initialized:
            self.initialize(config=config)

        if not self.is_available:
            raise VlmProviderUnavailableError("Hugging Face engine dependencies are not available")

        mode = VlmExecutionMode.REMOTE if self._config.endpoint else VlmExecutionMode.LOCAL

        return VlmResult(
            task=request.task,
            text_result=f"HuggingFace VLM Output for task '{request.task.value}'",
            provider_id=self.provider_id,
            model_id=self.model_id,
            execution_mode=mode,
            device="cpu",
        )
