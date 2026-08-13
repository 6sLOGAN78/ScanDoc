"""
Abstract Base Class contract for Vision-Language Model providers.
"""

from abc import ABC, abstractmethod
from typing import Iterator, List, Optional

from scandoc.providers.vlm.models import VlmConfig, VlmRequest, VlmResult
from scandoc.providers.vlm.taxonomy import ProviderType


class BaseVlmProvider(ABC):
    """
    Abstract Base Class for Vision-Language Model (VLM) providers.
    
    Decouples multimodal visual reasoning models (local VLMs, Hugging Face models, Remote APIs, OpenAI-compatible APIs)
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
        """Return True if engine dependencies and model weights are available."""
        return True

    @abstractmethod
    def initialize(self, config: Optional[VlmConfig] = None) -> None:
        """Initialize provider models and configuration."""
        pass

    @abstractmethod
    def analyze(self, request: VlmRequest, config: Optional[VlmConfig] = None) -> VlmResult:
        """
        Analyze multimodal document content (image + prompt + text context) and return VlmResult.
        """
        pass

    def analyze_batch(
        self,
        requests: List[VlmRequest],
        config: Optional[VlmConfig] = None,
    ) -> List[VlmResult]:
        """
        Perform batch VLM analysis.
        """
        return [self.analyze(req, config=config) for req in requests]

    def analyze_stream(
        self,
        request: VlmRequest,
        config: Optional[VlmConfig] = None,
    ) -> Iterator[str]:
        """
        Optional streaming inference interface yielding generated text tokens.
        """
        res = self.analyze(request, config=config)
        if res.text_result:
            yield res.text_result

    def health_check(self) -> bool:
        """Return True if provider engine is healthy and operational."""
        return self.is_available

    def shutdown(self) -> None:
        """Release allocated model sessions or resources."""
        pass

    def __enter__(self) -> "BaseVlmProvider":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown()
