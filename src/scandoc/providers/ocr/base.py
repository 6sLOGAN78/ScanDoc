"""
Abstract base class contract for all scanDOC OCR providers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, List, Optional, Union

from scandoc.providers.ocr.models import OcrConfig, OCRResult


class BaseOcrProvider(ABC):
    """
    Abstract Base Class for Optical Character Recognition (OCR) providers.
    
    Decouples underlying OCR libraries (RapidOCR, Tesseract, Surya, Paddle, Cloud APIs)
    from scanDOC DocumentIR assembly and pipeline logic.
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Return unique string identifier of provider (e.g., 'rapidocr', 'tesseract')."""
        pass

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Return specific model checkpoint identifier (e.g., 'PP-OCRv4')."""
        pass

    @property
    @abstractmethod
    def supported_languages(self) -> List[str]:
        """Return list of ISO language codes supported by provider (e.g. ['en', 'ch'])."""
        pass

    @property
    def is_available(self) -> bool:
        """Return True if required engine dependencies and model weights are available."""
        return True

    @abstractmethod
    def initialize(self, config: Optional[OcrConfig] = None) -> None:
        """Initialize provider models and configuration."""
        pass

    @abstractmethod
    def process_image(
        self,
        image_input: Union[str, Path, bytes, bytearray, BinaryIO],
        config: Optional[OcrConfig] = None,
    ) -> OCRResult:
        """
        Perform OCR on a single image input source.
        
        Args:
            image_input: Filepath, bytes buffer, or binary stream.
            config: Optional override configuration for this inference run.
            
        Returns:
            OCRResult object containing recognized text regions and bounding boxes.
        """
        pass

    def process_batch(
        self,
        image_inputs: List[Union[str, Path, bytes, bytearray, BinaryIO]],
        config: Optional[OcrConfig] = None,
    ) -> List[OCRResult]:
        """
        Perform batch OCR processing over multiple image input sources.
        
        Default implementation iterates over single image calls.
        Subclasses can override with hardware batching optimizations.
        """
        return [self.process_image(img, config=config) for img in image_inputs]

    def shutdown(self) -> None:
        """Release allocated engine resources or handles."""
        pass

    def __enter__(self) -> "BaseOcrProvider":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown()
