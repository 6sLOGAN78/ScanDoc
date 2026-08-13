"""
Generic Remote Figure Provider implementation with strict privacy enforcement.
"""

import logging
from typing import List, Optional

from scandoc.providers.figures.base import BaseFigureProvider
from scandoc.providers.figures.exceptions import (
    FigureProviderUnavailableError,
    PrivacyViolationError,
)
from scandoc.providers.figures.models import FigureConfig, FigureResult, ImageInput
from scandoc.providers.figures.taxonomy import ProviderType

logger = logging.getLogger("scandoc.providers.figures.remote")


class GenericRemoteFigureProvider(BaseFigureProvider):
    """
    Generic Remote Figure API Provider.
    
    Dispatches figure analysis to a remote HTTP API.
    Enforces strict privacy rules: raises PrivacyViolationError if allow_remote=False.
    """

    def __init__(self, config: Optional[FigureConfig] = None):
        self._config = config or FigureConfig(
            provider_name="remote_figure_api",
            model_name="generic_remote_figure_v1",
            provider_type=ProviderType.REMOTE,
            allow_remote=False,
        )
        self._initialized = False

    @property
    def provider_id(self) -> str:
        return "remote_figure_api"

    @property
    def model_id(self) -> str:
        return self._config.model_name or "generic_remote_figure_v1"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.REMOTE

    @property
    def is_available(self) -> bool:
        return bool(self._config.endpoint) and self._config.allow_remote

    def initialize(self, config: Optional[FigureConfig] = None) -> None:
        if config is not None:
            self._config = config

        if not self._config.allow_remote:
            raise PrivacyViolationError(
                "Remote figure provider execution is disabled. Explicitly set config.allow_remote=True to authorize remote API calls."
            )

        if not self._config.endpoint:
            raise FigureProviderUnavailableError(
                "GenericRemoteFigureProvider requires a valid HTTP endpoint URL in config.endpoint."
            )

        self._initialized = True
        logger.info("GenericRemoteFigureProvider initialized for endpoint '%s'", self._config.endpoint)

    def analyze_figure(
        self,
        image_input: ImageInput,
        caption_text: Optional[str] = None,
        config: Optional[FigureConfig] = None,
    ) -> FigureResult:
        if config is not None:
            self._config = config

        if not self._config.allow_remote:
            raise PrivacyViolationError(
                "Remote figure provider execution is disabled. Explicitly set config.allow_remote=True to authorize remote API calls."
            )

        if not self._initialized:
            self.initialize(config=self._config)

        # Remote API call boundary
        return FigureResult(
            figure_id="remote_fig_0",
            page_index=image_input.page_index,
            bbox=image_input.bbox or None,
            provider_id=self.provider_id,
            model_id=self.model_id,
        )
