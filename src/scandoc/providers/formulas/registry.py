"""
Central Formula Provider Registry and provider selection orchestrator with privacy enforcement.
"""

import logging
from typing import Dict, List, Optional

from scandoc.providers.formulas.base import BaseFormulaProvider
from scandoc.providers.formulas.exceptions import (
    FormulaProviderUnavailableError,
    PrivacyViolationError,
)
from scandoc.providers.formulas.huggingface_provider import HuggingFaceFormulaAdapter
from scandoc.providers.formulas.local_provider import LocalFormulaProvider
from scandoc.providers.formulas.models import FormulaConfig
from scandoc.providers.formulas.remote_provider import GenericRemoteFormulaProvider
from scandoc.providers.formulas.taxonomy import ProviderType

logger = logging.getLogger("scandoc.providers.formulas.registry")


class FormulaProviderRegistry:
    """
    Registry managing formula and mathematical content providers.
    Enforces privacy rules preventing un-authorized remote API execution.
    """

    def __init__(self, register_defaults: bool = True):
        self._providers: Dict[str, BaseFormulaProvider] = {}
        if register_defaults:
            self._register_default_providers()

    def _register_default_providers(self) -> None:
        defaults = [
            LocalFormulaProvider(),
            HuggingFaceFormulaAdapter(),
            GenericRemoteFormulaProvider(),
        ]
        for p in defaults:
            self.register(p)

    def register(self, provider: BaseFormulaProvider) -> None:
        """Register a formula provider instance."""
        pid = provider.provider_id.lower()
        if pid in self._providers:
            logger.warning("Overwriting registered formula provider '%s'", pid)
        self._providers[pid] = provider

    def unregister(self, provider_id: str) -> Optional[BaseFormulaProvider]:
        """Unregister a formula provider by ID."""
        pid = provider_id.lower()
        return self._providers.pop(pid, None)

    def get_provider(self, provider_id: str) -> BaseFormulaProvider:
        """Get registered formula provider by ID."""
        pid = provider_id.lower()
        if pid not in self._providers:
            raise FormulaProviderUnavailableError(f"No formula provider registered with ID '{provider_id}'")
        return self._providers[pid]

    def list_providers(self) -> List[BaseFormulaProvider]:
        """Return list of all registered formula providers."""
        return list(self._providers.values())

    def select_provider(self, config: Optional[FormulaConfig] = None) -> BaseFormulaProvider:
        """
        Select an available formula provider.
        Enforces privacy boundary: skips remote providers if allow_remote=False.
        """
        cfg = config or FormulaConfig()
        req_name = cfg.model_name.lower()

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

        raise FormulaProviderUnavailableError("No authorized formula provider available in registry")


# Global Singleton
default_formula_registry = FormulaProviderRegistry()
