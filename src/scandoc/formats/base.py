"""
Abstract base class contract for all document format providers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional, Set, Union

from scandoc.models.document import DocumentIR
from scandoc.formats.models import FormatDetectionResult, ProviderInfo


class BaseFormatProvider(ABC):
    """
    Abstract Base Class for Document Format Providers.
    
    Acts as the standard boundary interface converting format-specific document streams
    into unified scanDOC DocumentIR graphs.
    """

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return unique string identifier for format (e.g. 'pdf', 'docx')."""
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> Set[str]:
        """Return set of normalized file extensions including dot (e.g. {'.pdf'})."""
        pass

    @property
    @abstractmethod
    def supported_mime_types(self) -> Set[str]:
        """Return set of supported MIME types (e.g. {'application/pdf'})."""
        pass

    @property
    def is_fully_implemented(self) -> bool:
        """
        Return True if provider implements complete DocumentIR extraction,
        False if provider is a placeholder stub.
        """
        return False

    @property
    def description(self) -> str:
        """Return short provider description."""
        return f"{self.format_name.upper()} Format Provider"

    def can_process(
        self,
        source: Union[str, Path, bytes, bytearray, BinaryIO],
        detection: Optional[FormatDetectionResult] = None,
    ) -> bool:
        """
        Determine whether this provider can process the given input source.
        """
        if detection is not None:
            if detection.detected_format.lower() == self.format_name.lower():
                return True
            if detection.extension.lower() in self.supported_extensions:
                return True
            if detection.mime_type.lower() in self.supported_mime_types:
                return True
        return False

    @abstractmethod
    def parse(
        self,
        source: Union[str, Path, bytes, bytearray, BinaryIO],
        file_path: Optional[str] = None,
    ) -> DocumentIR:
        """
        Parse input document source and return a verified DocumentIR instance.
        """
        pass

    def get_info(self) -> ProviderInfo:
        """Return provider metadata summary."""
        return ProviderInfo(
            name=self.format_name,
            supported_extensions=sorted(list(self.supported_extensions)),
            supported_mime_types=sorted(list(self.supported_mime_types)),
            is_fully_implemented=self.is_fully_implemented,
            description=self.description,
        )
