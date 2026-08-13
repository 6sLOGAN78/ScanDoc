"""
Local Figure Provider implementation delegating hardware execution to ExecutionManager.
"""

import io
import logging
from pathlib import Path
import time
from typing import List, Optional
import uuid

from PIL import Image

from scandoc.acceleration.manager import default_execution_manager
from scandoc.models.geometry import BoundingBox
from scandoc.models.provenance import ProcessingStage, Provenance
from scandoc.providers.figures.base import BaseFigureProvider
from scandoc.providers.figures.exceptions import InvalidImageInputError
from scandoc.providers.figures.models import FigureConfig, FigureResult, ImageInput
from scandoc.providers.figures.taxonomy import FigureType, ProviderType

logger = logging.getLogger("scandoc.providers.figures.local")


class LocalFigureProvider(BaseFigureProvider):
    """
    Local Figure Analysis Provider.
    
    Performs local image metadata extraction, aspect-ratio analysis, and basic category classification.
    Delegates hardware device execution to scandoc ExecutionManager and DeviceContext.
    """

    def __init__(self, config: Optional[FigureConfig] = None):
        self._config = config or FigureConfig(provider_name="local_figure_analyzer", model_name="BasicFigureAnalyzer-v1", provider_type=ProviderType.LOCAL)
        self._initialized = False

    @property
    def provider_id(self) -> str:
        return "local_figure_analyzer"

    @property
    def model_id(self) -> str:
        return self._config.model_name or "BasicFigureAnalyzer-v1"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.LOCAL

    @property
    def is_available(self) -> bool:
        return True

    def initialize(self, config: Optional[FigureConfig] = None) -> None:
        if config is not None:
            self._config = config
        dev_ctx = default_execution_manager.select_device(self._config.device)
        logger.info("LocalFigureProvider initialized on device '%s'", dev_ctx.to_device_string())
        self._initialized = True

    def analyze_figure(
        self,
        image_input: ImageInput,
        caption_text: Optional[str] = None,
        config: Optional[FigureConfig] = None,
    ) -> FigureResult:
        if not self._initialized:
            self.initialize(config=config)

        start_time = time.perf_counter()

        # Extract image metadata
        img_bytes, width, height, fmt = self._extract_metadata(image_input)
        aspect_ratio = round(width / float(height), 3) if height > 0 else 1.0

        # Basic category heuristic based on dimensions/aspect ratio
        fig_type = FigureType.FIGURE
        if fmt in ("JPEG", "JPG"):
            fig_type = FigureType.PHOTOGRAPH
        elif aspect_ratio > 3.0 or aspect_ratio < 0.3:
            fig_type = FigureType.DIAGRAM

        bbox = image_input.bbox or BoundingBox(left=0.0, top=0.0, right=1.0, bottom=1.0, is_normalized=True)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        prov = Provenance(
            provider=self.provider_id,
            model=self.model_id,
            stage=ProcessingStage.POST_PROCESSING,
            confidence=0.95,
        )

        return FigureResult(
            figure_id=f"fig_{uuid.uuid4().hex[:8]}",
            page_index=image_input.page_index,
            bbox=bbox,
            figure_type=fig_type,
            confidence=0.95,
            description=f"Image ({width}x{height} px, {fmt})" if fmt else "Document Figure",
            associated_caption_text=caption_text,
            provider_id=self.provider_id,
            model_id=self.model_id,
            processing_time_ms=round(elapsed_ms, 2),
            provenance=prov,
            metadata={
                "width": str(width),
                "height": str(height),
                "format": str(fmt or "UNKNOWN"),
                "aspect_ratio": str(aspect_ratio),
                "source_type": image_input.source_type,
            },
        )

    def _extract_metadata(self, image_input: ImageInput) -> tuple[Optional[bytes], int, int, Optional[str]]:
        """Extract width, height, format, and bytes from ImageInput without unnecessary copies."""
        if image_input.width and image_input.height:
            return image_input.image_bytes, image_input.width, image_input.height, image_input.format

        if image_input.image_bytes:
            try:
                with Image.open(io.BytesIO(image_input.image_bytes)) as pil_img:
                    return image_input.image_bytes, pil_img.width, pil_img.height, pil_img.format
            except Exception as e:
                raise InvalidImageInputError(f"Failed to decode ImageInput bytes: {e}") from e

        if image_input.image_path:
            p = Path(image_input.image_path)
            if not p.exists():
                raise InvalidImageInputError(f"Image path not found: {image_input.image_path}")
            b = p.read_bytes()
            with Image.open(io.BytesIO(b)) as pil_img:
                return b, pil_img.width, pil_img.height, pil_img.format

        raise InvalidImageInputError("ImageInput contains no valid bytes or file path payload")
