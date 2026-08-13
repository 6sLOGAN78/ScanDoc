"""
Document Layout Analysis Subsystem for scanDOC.
"""

from scandoc.providers.layout.base import BaseLayoutProvider
from scandoc.providers.layout.converter import layout_result_to_document_ir
from scandoc.providers.layout.exceptions import (
    InvalidLayoutConfigError,
    LayoutError,
    LayoutInferenceError,
    LayoutInitializationError,
    LayoutModelError,
    LayoutProviderUnavailableError,
)
from scandoc.providers.layout.models import LayoutConfig, LayoutRegion, LayoutResult
from scandoc.providers.layout.registry import (
    LayoutProviderRegistry,
    default_layout_registry,
)
from scandoc.providers.layout.rtdetr_provider import RtDetrLayoutProvider
from scandoc.providers.layout.taxonomy import (
    DocLayNetMapper,
    LayoutCategory,
    PubLayNetMapper,
)

__all__ = [
    "BaseLayoutProvider",
    "RtDetrLayoutProvider",
    "LayoutProviderRegistry",
    "default_layout_registry",
    "LayoutCategory",
    "DocLayNetMapper",
    "PubLayNetMapper",
    "LayoutConfig",
    "LayoutRegion",
    "LayoutResult",
    "layout_result_to_document_ir",
    "LayoutError",
    "LayoutProviderUnavailableError",
    "LayoutModelError",
    "LayoutInferenceError",
    "InvalidLayoutConfigError",
    "LayoutInitializationError",
]
