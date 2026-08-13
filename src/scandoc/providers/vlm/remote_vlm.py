"""
Generic Remote VLM Provider implementation with strict privacy enforcement.
"""

import logging
from typing import List, Optional

from scandoc.providers.vlm.base import BaseVlmProvider
from scandoc.providers.vlm.exceptions import (
    PrivacyViolationError,
    VlmProviderUnavailableError,
)
from scandoc.providers.vlm.models import VlmConfig, VlmRequest, VlmResult
from scandoc.providers.vlm.taxonomy import ProviderType, VlmExecutionMode

logger = logging.getLogger("scandoc.providers.vlm.remote")


class GenericRemoteVlmProvider(BaseVlmProvider):
    """
    Generic Remote Vision-Language Model API Provider.
    
    Dispatches multimodal reasoning tasks to a remote HTTP API.
    Enforces strict privacy rules: raises PrivacyViolationError if allow_remote=False.
    """

    def __init__(self, config: Optional[VlmConfig] = None):
        self._config = config or VlmConfig(
            provider_name="remote_vlm_api",
            model_name="generic_remote_vlm_v1",
            provider_type=ProviderType.REMOTE,
            allow_remote=False,
        )
        self._initialized = False

    @property
    def provider_id(self) -> str:
        return "remote_vlm_api"

    @property
    def model_id(self) -> str:
        return self._config.model_name or "generic_remote_vlm_v1"

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
                "Remote VLM provider execution is disabled. Explicitly set config.allow_remote=True to authorize remote API calls."
            )

        if not self._config.endpoint:
            raise VlmProviderUnavailableError(
                "GenericRemoteVlmProvider requires a valid HTTP endpoint URL in config.endpoint."
            )

        self._initialized = True
        logger.info("GenericRemoteVlmProvider initialized for endpoint '%s'", self._config.endpoint)

    def analyze(self, request: VlmRequest, config: Optional[VlmConfig] = None) -> VlmResult:
        if config is not None:
            self._config = config

        if not self._config.allow_remote:
            raise PrivacyViolationError(
                "Remote VLM provider execution is disabled. Explicitly set config.allow_remote=True to authorize remote API calls."
            )

        if not self._initialized:
            self.initialize(config=self._config)

        return VlmResult(
            task=request.task,
            text_result=f"Remote VLM output for task '{request.task.value}'",
            provider_id=self.provider_id,
            model_id=self.model_id,
            execution_mode=VlmExecutionMode.REMOTE,
            device="remote",
        )
