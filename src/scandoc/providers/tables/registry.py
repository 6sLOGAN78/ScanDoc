"""
Central Table Provider Registry and provider selection orchestrator.
"""

import logging
from typing import Dict, List, Optional

from scandoc.providers.tables.base import BaseTableProvider
from scandoc.providers.tables.exceptions import TableProviderUnavailableError
from scandoc.providers.tables.models import TableStructureConfig
from scandoc.providers.tables.slanet_provider import SlaNetTableProvider

logger = logging.getLogger("scandoc.providers.tables.registry")


class TableProviderRegistry:
    """
    Registry managing table structure recognition providers.
    """

    def __init__(self, register_defaults: bool = True):
        self._providers: Dict[str, BaseTableProvider] = {}
        if register_defaults:
            self._register_default_providers()

    def _register_default_providers(self) -> None:
        defaults = [
            SlaNetTableProvider(),
        ]
        for p in defaults:
            self.register(p)

    def register(self, provider: BaseTableProvider) -> None:
        """Register a table structure provider."""
        pid = provider.provider_id.lower()
        if pid in self._providers:
            logger.warning("Overwriting registered table provider '%s'", pid)
        self._providers[pid] = provider

    def unregister(self, provider_id: str) -> Optional[BaseTableProvider]:
        """Unregister a table provider by ID."""
        pid = provider_id.lower()
        return self._providers.pop(pid, None)

    def get_provider(self, provider_id: str) -> BaseTableProvider:
        """Get registered table provider by ID."""
        pid = provider_id.lower()
        if pid not in self._providers:
            raise TableProviderUnavailableError(f"No table provider registered with ID '{provider_id}'")
        return self._providers[pid]

    def list_providers(self) -> List[BaseTableProvider]:
        """Return list of all registered table providers."""
        return list(self._providers.values())

    def select_provider(self, config: Optional[TableStructureConfig] = None) -> BaseTableProvider:
        """Select an available table structure provider."""
        cfg = config or TableStructureConfig()
        req_name = cfg.model_name.lower()

        for pid, provider in self._providers.items():
            if provider.is_available:
                return provider

        if self._providers:
            return next(iter(self._providers.values()))

        raise TableProviderUnavailableError("No table provider available in registry")


# Global Singleton
default_table_registry = TableProviderRegistry()
