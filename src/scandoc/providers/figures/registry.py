"""
Central Figure Provider Registry and provider selection orchestrator with privacy enforcement.
"""

import logging
from typing import Dict, List, Optional

from scandoc.providers.figures.base import BaseFigureProvider
from scandoc.providers.figures.exceptions import (
    FigureProviderUnavailableError,
    PrivacyViolationError,
)
from scandoc.providers.figures.huggingface_provider import HuggingFaceFigureAdapter
from scandoc.providers.figures.local_provider import LocalFigureProvider
from scandoc.providers.figures.models import FigureConfig
from scandoc.providers.figures.remote_provider import GenericRemoteFigureProvider
from scandoc.providers.figures.taxonomy import ProviderType

logger = logging.getLogger("scandoc.providers.figures.registry")


class FigureProviderRegistry:
    """
    Registry managing figure and image understanding providers.
    Enforces privacy rules preventing un-authorized remote API execution.
    """

    def __init__(self, register_defaults: bool = True):
        self._providers: Dict[str, BaseFigureProvider] = {}
        if register_defaults:
            self._register_default_providers()

    def _register_default_providers(self) -> None:
        defaults = [
            LocalFigureProvider(),
            HuggingFaceFigureAdapter(),
            GenericRemoteFigureProvider(),
        ]
        for p in defaults:
            self.register(p)

    def register(self, provider: BaseFigureProvider) -> None:
        """Register a figure provider instance."""
        pid = provider.provider_id.lower()
        if pid in self._providers:
            logger.warning("Overwriting registered figure provider '%s'", pid)
        self._providers[pid] = provider

    def unregister(self, provider_id: str) -> Optional[BaseFigureProvider]:
        """Unregister a figure provider by ID."""
        pid = provider_id.lower()
        return self._providers.pop(pid, None)

    def get_provider(self, provider_id: str) -> BaseFigureProvider:
        """Get registered figure provider by ID."""
        pid = provider_id.lower()
        if pid not in self._providers:
            raise FigureProviderUnavailableError(f"No figure provider registered with ID '{provider_id}'")
        return self._providers[pid]

    def list_providers(self) -> List[BaseFigureProvider]:
        """Return list of all registered figure providers."""
        return list(self._providers.values())

    def select_provider(self, config: Optional[FigureConfig] = None) -> BaseFigureProvider:
        """
        Select an available figure provider.
        Enforces privacy boundary: skips remote providers if allow_remote=False.
        """
        cfg = config or FigureConfig()
        req_name = cfg.model_name.lower()

        # Check explicit requested provider
        for pid, provider in self._providers.items():
            if provider.provider_type == ProviderType.REMOTE and not cfg.allow_remote:
                continue
            if provider.is_available:
                return provider

        # Fallback to local provider if available
        for pid, provider in self._providers.items():
            if provider.provider_type == ProviderType.LOCAL and provider.is_available:
                return provider

        raise FigureProviderUnavailableError("No authorized figure provider available in registry")


# Global Singleton
default_figure_registry = FigureProviderRegistry()
