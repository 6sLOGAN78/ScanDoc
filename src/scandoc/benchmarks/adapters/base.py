"""
Base class interface for benchmark adapters.
"""

from abc import ABC, abstractmethod
from typing import Optional

from scandoc.benchmarks.models import BenchmarkConversionResult


class BaseBenchmarkAdapter(ABC):
    """
    Abstract interface that all document engine benchmark adapters must implement.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name identifier of the document engine (e.g. 'scandoc', 'docling')."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Version string of the underlying engine."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the adapter's dependencies and runtime are available."""
        pass

    @abstractmethod
    def convert(self, file_path: str) -> BenchmarkConversionResult:
        """
        Execute document conversion and return structured benchmark result.
        
        Args:
            file_path: Path to target document file
            
        Returns:
            BenchmarkConversionResult with extracted text, tables, timing, and RAM footprint.
        """
        pass
