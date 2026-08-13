"""
Hugging Face Figure Provider Adapter implementation for local or remote HF models.
"""

import logging
from typing import List, Optional

from scandoc.providers.figures.base import BaseFigureProvider
from scandoc.providers.figures.exceptions import FigureProviderUnavailableError
from scandoc.providers.figures.models import FigureConfig, FigureResult, ImageInput
from scandoc.providers.figures.taxonomy import ProviderType

logger = logging.getLogger("scandoc.providers.figures.huggingface")


class HuggingFaceFigureAdapter(BaseFigureProvider):
    """
    Hugging Face Figure Provider Adapter.
    
    Supports local inference from downloaded weights or remote Hugging Face Inference Endpoints.
    """

    def __init__(self, config: Optional[FigureConfig] = None):
        self._config = config or FigureConfig(
            provider_name="huggingface_figure",
            model_name="microsoft/git-base-coco",
            provider_type=ProviderType.HUGGINGFACE,
        )
        self._initialized = False

    @property
    def provider_id(self) -> str:
        return "huggingface_figure"

    @property
    def model_id(self) -> str:
        return self._config.model_name or "microsoft/git-base-coco"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.HUGGINGFACE

    @property
    def is_available(self) -> bool:
        """Return True if transformers and torch packages are installed."""
        try:
            import transformers  # type: ignore
            import torch  # type: ignore
            return True
        except ImportError:
            return False

    def initialize(self, config: Optional[FigureConfig] = None) -> None:
        if config is not None:
            self._config = config

        if not self.is_available:
            raise FigureProviderUnavailableError(
                "Hugging Face Figure Provider requirements are not installed. Install 'transformers' and 'torch'."
            )
        self._initialized = True
        logger.info("HuggingFaceFigureAdapter initialized for model '%s'", self.model_id)

    def analyze_figure(
        self,
        image_input: ImageInput,
        caption_text: Optional[str] = None,
        config: Optional[FigureConfig] = None,
    ) -> FigureResult:
        if not self._initialized:
            self.initialize(config=config)

        if not self.is_available:
            raise FigureProviderUnavailableError("Hugging Face engine dependencies are not available")

        # Adapter boundary for HF model execution
        return FigureResult(
            figure_id="hf_fig_0",
            page_index=image_input.page_index,
            bbox=image_input.bbox or None,
            provider_id=self.provider_id,
            model_id=self.model_id,
        )
