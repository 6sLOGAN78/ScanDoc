"""
Central VLM Provider Registry and provider selection orchestrator with privacy enforcement.
"""

import logging
from typing import Dict, List, Optional

from scandoc.providers.vlm.base import BaseVlmProvider
from scandoc.providers.vlm.exceptions import (
    PrivacyViolationError,
    VlmProviderUnavailableError,
)
from scandoc.providers.vlm.huggingface_vlm import HuggingFaceVlmAdapter
from scandoc.providers.vlm.local_vlm import LocalVlmProvider
from scandoc.providers.vlm.models import VlmConfig
from scandoc.providers.vlm.openai_vlm import OpenAiCompatibleVlmProvider
from scandoc.providers.vlm.remote_vlm import GenericRemoteVlmProvider
from scandoc.providers.vlm.taxonomy import ProviderType

logger = logging.getLogger("scandoc.providers.vlm.registry")


class VlmProviderRegistry:
    """
    Registry managing Vision-Language Model providers.
    Enforces privacy rules preventing unauthorized remote VLM API execution.
    """

    def __init__(self, register_defaults: bool = True):
        self._providers: Dict[str, BaseVlmProvider] = {}
        if register_defaults:
            self._register_default_providers()

    def _register_default_providers(self) -> None:
        defaults = [
            LocalVlmProvider(),
            HuggingFaceVlmAdapter(),
            GenericRemoteVlmProvider(),
            OpenAiCompatibleVlmProvider(),
        ]
        for p in defaults:
            self.register(p)

    def register(self, provider: BaseVlmProvider) -> None:
        """Register a VLM provider instance."""
        pid = provider.provider_id.lower()
        if pid in self._providers:
            logger.warning("Overwriting registered VLM provider '%s'", pid)
        self._providers[pid] = provider

    def unregister(self, provider_id: str) -> Optional[BaseVlmProvider]:
        """Unregister a VLM provider by ID."""
        pid = provider_id.lower()
        return self._providers.pop(pid, None)

    def get_provider(self, provider_id: str) -> BaseVlmProvider:
        """Get registered VLM provider by ID."""
        pid = provider_id.lower()
        if pid not in self._providers:
            raise VlmProviderUnavailableError(f"No VLM provider registered with ID '{provider_id}'")
        return self._providers[pid]

    def list_providers(self) -> List[BaseVlmProvider]:
        """Return list of all registered VLM providers."""
        return list(self._providers.values())

    def select_provider(self, config: Optional[VlmConfig] = None) -> BaseVlmProvider:
        """
        Select an available VLM provider.
        Enforces privacy boundary: skips remote providers if allow_remote=False.
        """
        cfg = config or VlmConfig()

        # Check requested provider
        for pid, provider in self._providers.items():
            if provider.provider_type == ProviderType.REMOTE and not cfg.allow_remote:
                continue
            if provider.is_available:
                return provider

        # Fallback to local provider if available
        for pid, provider in self._providers.items():
            if provider.provider_type == ProviderType.LOCAL and provider.is_available:
                return provider

        raise VlmProviderUnavailableError("No authorized VLM provider available in registry")


# Global Singleton
default_vlm_registry = VlmProviderRegistry()
