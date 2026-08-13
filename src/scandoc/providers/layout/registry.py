"""
Central Layout Provider Registry and provider selection orchestrator.
"""

import logging
from typing import Dict, List, Optional

from scandoc.providers.layout.base import BaseLayoutProvider
from scandoc.providers.layout.exceptions import LayoutProviderUnavailableError
from scandoc.providers.layout.models import LayoutConfig
from scandoc.providers.layout.rtdetr_provider import RtDetrLayoutProvider

logger = logging.getLogger("scandoc.providers.layout.registry")


class LayoutProviderRegistry:
    """
    Registry for managing document layout analysis providers.
    """

    def __init__(self, register_defaults: bool = True):
        self._providers: Dict[str, BaseLayoutProvider] = {}
        if register_defaults:
            self._register_default_providers()

    def _register_default_providers(self) -> None:
        defaults = [
            RtDetrLayoutProvider(),
        ]
        for p in defaults:
            self.register(p)

    def register(self, provider: BaseLayoutProvider) -> None:
        """Register a layout provider instance."""
        pid = provider.provider_id.lower()
        if pid in self._providers:
            logger.warning("Overwriting registered layout provider '%s'", pid)
        self._providers[pid] = provider

    def unregister(self, provider_id: str) -> Optional[BaseLayoutProvider]:
        """Unregister a layout provider by ID."""
        pid = provider_id.lower()
        return self._providers.pop(pid, None)

    def get_provider(self, provider_id: str) -> BaseLayoutProvider:
        """Get registered layout provider by ID."""
        pid = provider_id.lower()
        if pid not in self._providers:
            raise LayoutProviderUnavailableError(f"No layout provider registered with ID '{provider_id}'")
        return self._providers[pid]

    def list_providers(self) -> List[BaseLayoutProvider]:
        """Return list of all registered layout providers."""
        return list(self._providers.values())

    def select_provider(self, config: Optional[LayoutConfig] = None) -> BaseLayoutProvider:
        """
        Select an available layout provider.
        """
        cfg = config or LayoutConfig()
        req_name = cfg.model_name.lower()

        for pid, provider in self._providers.items():
            if provider.is_available:
                return provider

        # Return registered provider boundary if available
        if self._providers:
            return next(iter(self._providers.values()))

        raise LayoutProviderUnavailableError("No layout provider available in registry")


# Global Singleton
default_layout_registry = LayoutProviderRegistry()
