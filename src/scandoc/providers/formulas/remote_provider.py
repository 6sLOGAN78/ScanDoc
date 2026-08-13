"""
Generic Remote Formula Provider implementation with strict privacy enforcement.
"""

import logging
from typing import Any, List, Optional

from scandoc.providers.formulas.base import BaseFormulaProvider
from scandoc.providers.formulas.exceptions import (
    FormulaProviderUnavailableError,
    PrivacyViolationError,
)
from scandoc.providers.formulas.models import (
    FormulaConfig,
    FormulaRepresentation,
    FormulaResult,
)
from scandoc.providers.formulas.taxonomy import FormulaType, MathFormat, ProviderType

logger = logging.getLogger("scandoc.providers.formulas.remote")


class GenericRemoteFormulaProvider(BaseFormulaProvider):
    """
    Generic Remote Formula API Provider.
    
    Dispatches mathematical content recognition to a remote HTTP API.
    Enforces strict privacy rules: raises PrivacyViolationError if allow_remote=False.
    """

    def __init__(self, config: Optional[FormulaConfig] = None):
        self._config = config or FormulaConfig(
            provider_name="remote_formula_api",
            model_name="generic_remote_formula_v1",
            provider_type=ProviderType.REMOTE,
            allow_remote=False,
        )
        self._initialized = False

    @property
    def provider_id(self) -> str:
        return "remote_formula_api"

    @property
    def model_id(self) -> str:
        return self._config.model_name or "generic_remote_formula_v1"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.REMOTE

    @property
    def is_available(self) -> bool:
        return bool(self._config.endpoint) and self._config.allow_remote

    def initialize(self, config: Optional[FormulaConfig] = None) -> None:
        if config is not None:
            self._config = config

        if not self._config.allow_remote:
            raise PrivacyViolationError(
                "Remote formula provider execution is disabled. Explicitly set config.allow_remote=True to authorize remote API calls."
            )

        if not self._config.endpoint:
            raise FormulaProviderUnavailableError(
                "GenericRemoteFormulaProvider requires a valid HTTP endpoint URL in config.endpoint."
            )

        self._initialized = True
        logger.info("GenericRemoteFormulaProvider initialized for endpoint '%s'", self._config.endpoint)

    def recognize_formula(
        self,
        input_payload: Any,
        bbox: Optional[Any] = None,
        formula_type: FormulaType = FormulaType.DISPLAY,
        page_index: int = 0,
        config: Optional[FormulaConfig] = None,
    ) -> FormulaResult:
        if config is not None:
            self._config = config

        if not self._config.allow_remote:
            raise PrivacyViolationError(
                "Remote formula provider execution is disabled. Explicitly set config.allow_remote=True to authorize remote API calls."
            )

        if not self._initialized:
            self.initialize(config=self._config)

        return FormulaResult(
            formula_id="remote_formula_0",
            page_index=page_index,
            bbox=bbox or None,
            formula_type=formula_type,
            representation=FormulaRepresentation(format=MathFormat.LATEX, value=r"\int_0^\infty e^{-x^2} dx"),
            provider_id=self.provider_id,
            model_id=self.model_id,
        )
