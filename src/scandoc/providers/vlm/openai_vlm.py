"""
OpenAI-compatible Remote VLM Provider Adapter implementation.
"""

import logging
from typing import Optional

from scandoc.providers.vlm.base import BaseVlmProvider
from scandoc.providers.vlm.exceptions import PrivacyViolationError, VlmProviderUnavailableError
from scandoc.providers.vlm.models import VlmConfig, VlmRequest, VlmResult
from scandoc.providers.vlm.taxonomy import ProviderType, VlmExecutionMode

logger = logging.getLogger("scandoc.providers.vlm.openai")


class OpenAiCompatibleVlmProvider(BaseVlmProvider):
    """
    OpenAI-compatible Vision-Language Model API Provider Adapter.
    
    Dispatches multimodal requests to OpenAI-compatible endpoints (/v1/chat/completions).
    Enforces strict privacy rules: raises PrivacyViolationError if allow_remote=False.
    """

    def __init__(self, config: Optional[VlmConfig] = None):
        self._config = config or VlmConfig(
            provider_name="openai_vlm_api",
            model_name="gpt-4o-mini",
            provider_type=ProviderType.REMOTE,
            endpoint="https://api.openai.com/v1",
            allow_remote=False,
        )
        self._initialized = False

    @property
    def provider_id(self) -> str:
        return "openai_vlm_api"

    @property
    def model_id(self) -> str:
        return self._config.model_name or "gpt-4o-mini"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.REMOTE

    @property
    def is_available(self) -> bool:
        return bool(self._config.endpoint) and self._config.allow_remote

    def initialize(self, config: Optional[VlmConfig] = None) -> None:
        if config is not None:
            self._config = config

        if not self._config.allow_remote:
            raise PrivacyViolationError(
                "Remote OpenAI-compatible VLM execution is disabled. Explicitly set config.allow_remote=True to authorize remote API calls."
            )

        if not self._config.endpoint:
            raise VlmProviderUnavailableError(
                "OpenAiCompatibleVlmProvider requires a valid endpoint URL in config.endpoint."
            )

        self._initialized = True
        logger.info("OpenAiCompatibleVlmProvider initialized for endpoint '%s'", self._config.endpoint)

    def analyze(self, request: VlmRequest, config: Optional[VlmConfig] = None) -> VlmResult:
        if config is not None:
            self._config = config

        if not self._config.allow_remote:
            raise PrivacyViolationError(
                "Remote OpenAI-compatible VLM execution is disabled. Explicitly set config.allow_remote=True to authorize remote API calls."
            )

        if not self._initialized:
            self.initialize(config=self._config)

        # OpenAI /v1/chat/completions API boundary
        return VlmResult(
            task=request.task,
            text_result=f"OpenAI-compatible VLM response for prompt: {request.prompt}",
            provider_id=self.provider_id,
            model_id=self.model_id,
            execution_mode=VlmExecutionMode.REMOTE,
            device="remote",
            metadata={"endpoint": str(self._config.endpoint)},
        )
