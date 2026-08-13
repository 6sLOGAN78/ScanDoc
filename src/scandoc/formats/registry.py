"""
Central format registry and provider lookup orchestrator for scanDOC.
"""

import logging
from pathlib import Path
from typing import BinaryIO, Dict, List, Optional, Union

from scandoc.models.document import DocumentIR
from scandoc.formats.base import BaseFormatProvider
from scandoc.formats.detector import FormatDetector
from scandoc.formats.exceptions import (
    ProviderExtractionError,
    ProviderUnavailableError,
    UnsupportedFormatError,
)
from scandoc.formats.models import FormatDetectionResult, ProviderInfo
from scandoc.formats.providers import (
    DOCXFormatProvider,
    HTMLFormatProvider,
    ImageFormatProvider,
    MarkdownFormatProvider,
    PDFFormatProvider,
    PPTXFormatProvider,
    TXTFormatProvider,
)

logger = logging.getLogger("scandoc.formats.registry")


class FormatRegistry:
    """
    Registry managing document format providers and orchestrating ingestion.
    """

    def __init__(self, register_defaults: bool = True):
        self._providers: Dict[str, BaseFormatProvider] = {}
        if register_defaults:
            self._register_default_providers()

    def _register_default_providers(self) -> None:
        """Register default format providers for PDF, DOCX, PPTX, HTML, Image, TXT, Markdown."""
        defaults = [
            PDFFormatProvider(),
            DOCXFormatProvider(),
            PPTXFormatProvider(),
            HTMLFormatProvider(),
            ImageFormatProvider(),
            TXTFormatProvider(),
            MarkdownFormatProvider(),
        ]
        for provider in defaults:
            self.register(provider)

    def register(self, provider: BaseFormatProvider) -> None:
        """
        Register a new or custom format provider.
        
        Args:
            provider: Instance of BaseFormatProvider subclass.
        """
        fmt_name = provider.format_name.lower()
        self._providers[fmt_name] = provider
        logger.debug("Registered format provider: '%s' (%s)", fmt_name, provider.description)

    def unregister(self, format_name: str) -> Optional[BaseFormatProvider]:
        """
        Unregister an existing format provider by name.
        
        Args:
            format_name: String identifier of format provider to remove.
            
        Returns:
            The removed provider instance if found, else None.
        """
        fmt_clean = format_name.lower()
        removed = self._providers.pop(fmt_clean, None)
        if removed:
            logger.debug("Unregistered format provider: '%s'", fmt_clean)
        return removed

    def list_providers(self) -> List[ProviderInfo]:
        """Return metadata for all currently registered format providers."""
        return [provider.get_info() for provider in self._providers.values()]

    def detect_format(
        self,
        source: Union[str, Path, bytes, bytearray, BinaryIO],
        override_format: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> FormatDetectionResult:
        """
        Detect input document format using magic bytes, extensions, and overrides.
        """
        return FormatDetector.detect(source, override_format=override_format, file_path=file_path)

    def get_provider_for(
        self,
        source: Union[str, Path, bytes, bytearray, BinaryIO],
        override_format: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> BaseFormatProvider:
        """
        Detect format and return the matching registered provider.
        
        Raises:
            UnsupportedFormatError: If no provider is registered for detected format.
        """
        detection = self.detect_format(source, override_format=override_format, file_path=file_path)
        fmt_key = detection.detected_format.lower()
        
        # Check direct format key lookup
        if fmt_key in self._providers:
            provider = self._providers[fmt_key]
            if provider.can_process(source, detection):
                return provider

        # Fallback search across all registered providers
        for provider in self._providers.values():
            if provider.can_process(source, detection):
                return provider

        raise UnsupportedFormatError(
            f"No registered format provider available for detected format '{detection.detected_format}'"
        )

    def parse(
        self,
        source: Union[str, Path, bytes, bytearray, BinaryIO],
        override_format: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> DocumentIR:
        """
        Detect document format, select provider, and parse input into DocumentIR.
        
        Raises:
            UnsupportedFormatError: If format is not supported or provider not found.
            ProviderExtractionError: If provider is a stub or fails during parsing.
        """
        provider = self.get_provider_for(source, override_format=override_format, file_path=file_path)
        
        if not provider.is_fully_implemented:
            raise ProviderExtractionError(
                f"Format provider for '{provider.format_name}' is registered as a placeholder stub "
                f"and is not yet fully implemented."
            )

        return provider.parse(source, file_path=file_path)


# Default global registry singleton
default_registry = FormatRegistry()
