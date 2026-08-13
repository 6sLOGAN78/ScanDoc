"""
Central OCR Provider Registry and deterministic provider selection orchestrator.
"""

import logging
from typing import Dict, List, Optional

from scandoc.providers.ocr.base import BaseOcrProvider
from scandoc.providers.ocr.exceptions import (
    OcrError,
    OcrProviderUnavailableError,
)
from scandoc.providers.ocr.huggingface_adapter import HuggingFaceOcrAdapter
from scandoc.providers.ocr.models import OcrCapability, OcrProviderConfig
from scandoc.providers.ocr.rapidocr_provider import RapidOCRProvider
from scandoc.providers.ocr.remote_provider import GenericRemoteOcrProvider
from scandoc.providers.ocr.tesseract_provider import TesseractProvider

logger = logging.getLogger("scandoc.providers.ocr.registry")


class OcrProviderRegistry:
    """
    Registry for managing OCR providers and selecting available engines.
    """

    def __init__(self, register_defaults: bool = True):
        self._providers: Dict[str, BaseOcrProvider] = {}
        if register_defaults:
            self._register_default_providers()

    def _register_default_providers(self) -> None:
        """Register default providers: RapidOCR, Tesseract, Generic Remote, HuggingFace."""
        defaults = [
            RapidOCRProvider(),
            TesseractProvider(),
            GenericRemoteOcrProvider(),
            HuggingFaceOcrAdapter(),
        ]
        for p in defaults:
            self.register(p)

    def register(self, provider: BaseOcrProvider) -> None:
        """
        Register an OCR provider instance.
        
        Args:
            provider: Instance of BaseOcrProvider subclass.
        """
        pid = provider.provider_id.lower()
        if pid in self._providers:
            logger.warning("Overwriting registered OCR provider '%s'", pid)
        self._providers[pid] = provider
        logger.debug("Registered OCR provider: '%s' (available=%s)", pid, provider.is_available)

    def unregister(self, provider_id: str) -> Optional[BaseOcrProvider]:
        """
        Unregister an OCR provider by ID.
        """
        pid = provider_id.lower()
        removed = self._providers.pop(pid, None)
        if removed:
            logger.debug("Unregistered OCR provider '%s'", pid)
        return removed

    def get_provider(self, provider_id: str) -> BaseOcrProvider:
        """
        Retrieve registered provider instance by ID.
        
        Raises:
            OcrProviderUnavailableError: If provider ID is not registered.
        """
        pid = provider_id.lower()
        if pid not in self._providers:
            raise OcrProviderUnavailableError(f"No OCR provider registered with ID '{provider_id}'")
        return self._providers[pid]

    def list_providers(self) -> List[BaseOcrProvider]:
        """Return list of all registered OCR provider instances."""
        return list(self._providers.values())

    def list_capabilities(self) -> List[OcrCapability]:
        """Return declared capabilities of all registered OCR providers."""
        return [p.capabilities for p in self._providers.values()]

    def select_provider(
        self,
        config: Optional[OcrProviderConfig] = None,
        fallback_chain: Optional[List[str]] = None,
    ) -> BaseOcrProvider:
        """
        Deterministically select an available OCR provider based on configuration and fallback chain.
        
        Args:
            config: OcrProviderConfig specifying requested provider_name and parameters.
            fallback_chain: Optional list of fallback provider IDs (e.g. ['rapidocr', 'tesseract']).
            
        Returns:
            An available BaseOcrProvider instance.
            
        Raises:
            OcrProviderUnavailableError: If no requested or fallback provider is available.
        """
        cfg = config or OcrProviderConfig()
        req_name = cfg.provider_name.lower()

        # Strategy 1: Explicit Requested Provider
        if req_name != "auto" and req_name in self._providers:
            provider = self._providers[req_name]
            if provider.is_available:
                return provider
            logger.info("Requested OCR provider '%s' is unavailable. Evaluating fallback chain.", req_name)

        # Strategy 2: Fallback Chain Evaluation
        chain = fallback_chain or ["rapidocr", "tesseract", "remote_http"]
        for pid in chain:
            pid_clean = pid.lower()
            if pid_clean in self._providers:
                provider = self._providers[pid_clean]
                if provider.is_available:
                    logger.info("Selected fallback OCR provider '%s'", pid_clean)
                    return provider

        # Strategy 3: Auto-Selection across any available provider
        for provider in self._providers.values():
            if provider.is_available:
                logger.info("Auto-selected available OCR provider '%s'", provider.provider_id)
                return provider

        raise OcrProviderUnavailableError(
            f"No available OCR provider found for request '{req_name}'. Registered providers: {list(self._providers.keys())}"
        )


# Global OCR Registry Singleton
default_ocr_registry = OcrProviderRegistry()
