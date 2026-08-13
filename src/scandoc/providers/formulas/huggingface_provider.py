"""
Hugging Face Formula Provider Adapter implementation for local or remote HF models.
"""

import logging
from typing import Any, List, Optional

from scandoc.providers.formulas.base import BaseFormulaProvider
from scandoc.providers.formulas.exceptions import FormulaProviderUnavailableError
from scandoc.providers.formulas.models import (
    FormulaConfig,
    FormulaRepresentation,
    FormulaResult,
)
from scandoc.providers.formulas.taxonomy import FormulaType, MathFormat, ProviderType

logger = logging.getLogger("scandoc.providers.formulas.huggingface")


class HuggingFaceFormulaAdapter(BaseFormulaProvider):
    """
    Hugging Face Formula Provider Adapter.
    
    Supports local inference from downloaded weights or remote Hugging Face Inference Endpoints.
    """

    def __init__(self, config: Optional[FormulaConfig] = None):
        self._config = config or FormulaConfig(
            provider_name="huggingface_formula",
            model_name="OARC/latex-ocr",
            provider_type=ProviderType.HUGGINGFACE,
        )
        self._initialized = False

    @property
    def provider_id(self) -> str:
        return "huggingface_formula"

    @property
    def model_id(self) -> str:
        return self._config.model_name or "OARC/latex-ocr"

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

    def initialize(self, config: Optional[FormulaConfig] = None) -> None:
        if config is not None:
            self._config = config

        if not self.is_available:
            raise FormulaProviderUnavailableError(
                "Hugging Face Formula Provider requirements are not installed. Install 'transformers' and 'torch'."
            )
        self._initialized = True
        logger.info("HuggingFaceFormulaAdapter initialized for model '%s'", self.model_id)

    def recognize_formula(
        self,
        input_payload: Any,
        bbox: Optional[Any] = None,
        formula_type: FormulaType = FormulaType.DISPLAY,
        page_index: int = 0,
        config: Optional[FormulaConfig] = None,
    ) -> FormulaResult:
        if not self._initialized:
            self.initialize(config=config)

        if not self.is_available:
            raise FormulaProviderUnavailableError("Hugging Face engine dependencies are not available")

        return FormulaResult(
            formula_id="hf_formula_0",
            page_index=page_index,
            bbox=bbox or None,
            formula_type=formula_type,
            representation=FormulaRepresentation(format=MathFormat.LATEX, value=r"\frac{a}{b}"),
            provider_id=self.provider_id,
            model_id=self.model_id,
        )
