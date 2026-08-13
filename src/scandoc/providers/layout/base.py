"""
Abstract Base Class contract for document layout analysis providers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, List, Optional, Union

from scandoc.providers.layout.models import LayoutConfig, LayoutResult
from scandoc.providers.layout.taxonomy import LayoutCategory


class BaseLayoutProvider(ABC):
    """
    Abstract Base Class for Document Layout Analysis providers.
    
    Decouples layout detection models (RT-DETR, YOLO, LayoutLM, Surya, Cloud APIs)
    from scanDOC DocumentIR assembly and pipeline logic.
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Return unique provider identifier (e.g. 'rt_detr_layout')."""
        pass

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Return specific model checkpoint name (e.g. 'RT-DETR-DocLayNet')."""
        pass

    @property
    @abstractmethod
    def supported_categories(self) -> List[LayoutCategory]:
        """Return list of LayoutCategories supported by this provider."""
        pass

    @property
    def is_available(self) -> bool:
        """Return True if required engine dependencies and model weights are available."""
        return True

    @abstractmethod
    def initialize(self, config: Optional[LayoutConfig] = None) -> None:
        """Initialize provider models and configuration."""
        pass

    @abstractmethod
    def detect_layout(
        self,
        image_input: Union[str, Path, bytes, bytearray, BinaryIO],
        page_index: int = 0,
        config: Optional[LayoutConfig] = None,
    ) -> LayoutResult:
        """
        Perform layout detection over a document page image.
        
        Args:
            image_input: File path, bytes buffer, or binary stream of page image.
            page_index: Target 0-indexed document page number.
            config: Optional override configuration for this inference run.
            
        Returns:
            LayoutResult containing detected LayoutRegions.
        """
        pass

    def detect_batch(
        self,
        image_inputs: List[Union[str, Path, bytes, bytearray, BinaryIO]],
        config: Optional[LayoutConfig] = None,
    ) -> List[LayoutResult]:
        """
        Perform batch layout detection over multiple document page images.
        """
        return [
            self.detect_layout(img, page_index=idx, config=config)
            for idx, img in enumerate(image_inputs)
        ]

    def shutdown(self) -> None:
        """Release allocated model sessions or resources."""
        pass

    def __enter__(self) -> "BaseLayoutProvider":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown()
