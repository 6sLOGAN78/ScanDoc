"""
Abstract Base Class contract for formula and mathematical content providers.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from scandoc.models.geometry import BoundingBox
from scandoc.providers.formulas.models import FormulaConfig, FormulaResult
from scandoc.providers.formulas.taxonomy import FormulaType, ProviderType


class BaseFormulaProvider(ABC):
    """
    Abstract Base Class for Formula & Mathematical Content providers.
    
    Decouples mathematical equation recognition models (TeXify, Pix2Text, Latexify, HF models, Remote APIs)
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
    def initialize(self, config: Optional[FormulaConfig] = None) -> None:
        """Initialize provider models and configuration."""
        pass

    @abstractmethod
    def recognize_formula(
        self,
        input_payload: Any,
        bbox: Optional[BoundingBox] = None,
        formula_type: FormulaType = FormulaType.DISPLAY,
        page_index: int = 0,
        config: Optional[FormulaConfig] = None,
    ) -> FormulaResult:
        """
        Recognize mathematical expression from image region or raw text input.
        """
        pass

    def recognize_batch(
        self,
        inputs: List[Any],
        config: Optional[FormulaConfig] = None,
    ) -> List[FormulaResult]:
        """
        Perform batch formula recognition.
        """
        return [
            self.recognize_formula(inp, page_index=idx, config=config)
            for idx, inp in enumerate(inputs)
        ]

    def shutdown(self) -> None:
        """Release allocated model sessions or resources."""
        pass

    def __enter__(self) -> "BaseFormulaProvider":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown()
