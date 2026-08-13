"""
Abstract Base Class contract for figure, image, and caption understanding providers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from scandoc.providers.figures.models import FigureConfig, FigureResult, ImageInput
from scandoc.providers.figures.taxonomy import ProviderType


class BaseFigureProvider(ABC):
    """
    Abstract Base Class for Figure, Image, and Caption Understanding providers.
    
    Decouples image understanding models (local classifiers, Hugging Face models, Remote APIs)
    from scanDOC DocumentIR assembly and pipeline logic.
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Return unique provider identifier."""
        pass

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Return specific model checkpoint name."""
        pass

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Return provider type (LOCAL, HUGGINGFACE, REMOTE)."""
        pass

    @property
    def is_available(self) -> bool:
        """Return True if required dependencies and model weights are available."""
        return True

    @abstractmethod
    def initialize(self, config: Optional[FigureConfig] = None) -> None:
        """Initialize provider models and configuration."""
        pass

    @abstractmethod
    def analyze_figure(
        self,
        image_input: ImageInput,
        caption_text: Optional[str] = None,
        config: Optional[FigureConfig] = None,
    ) -> FigureResult:
        """
        Analyze an input image payload and return structured FigureResult.
        """
        pass

    def analyze_batch(
        self,
        image_inputs: List[ImageInput],
        config: Optional[FigureConfig] = None,
    ) -> List[FigureResult]:
        """
        Perform batch figure analysis.
        """
        return [self.analyze_figure(img, config=config) for img in image_inputs]

    def shutdown(self) -> None:
        """Release allocated model sessions or resources."""
        pass

    def __enter__(self) -> "BaseFigureProvider":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown()
