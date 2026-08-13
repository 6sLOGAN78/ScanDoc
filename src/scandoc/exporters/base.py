"""
Abstract base class for all DocumentIR exporters.
"""

from abc import ABC, abstractmethod
from typing import Optional

from scandoc.exporters.models import ExportOptions, ExportResult
from scandoc.models import DocumentIR


class BaseExporter(ABC):
    """
    Abstract interface for provider-independent DocumentIR exporters.
    """

    @property
    @abstractmethod
    def format_id(self) -> str:
        """Unique string identifier for this exporter (e.g., 'markdown', 'html')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of exporter capabilities."""
        pass

    @abstractmethod
    def export(
        self,
        document: DocumentIR,
        options: Optional[ExportOptions] = None,
    ) -> ExportResult:
        """
        Export DocumentIR into formatted string or binary representation.
        """
        pass
