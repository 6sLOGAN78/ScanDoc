"""
Figure, Image & Caption Understanding Subsystem for scanDOC.
"""

from scandoc.providers.figures.base import BaseFigureProvider
from scandoc.providers.figures.caption import CaptionAssociator
from scandoc.providers.figures.converter import figure_result_to_document_ir
from scandoc.providers.figures.exceptions import (
    FigureError,
    FigureInferenceError,
    FigureProviderUnavailableError,
    InvalidImageInputError,
    PrivacyViolationError,
)
from scandoc.providers.figures.huggingface_provider import HuggingFaceFigureAdapter
from scandoc.providers.figures.local_provider import LocalFigureProvider
from scandoc.providers.figures.models import FigureConfig, FigureResult, ImageInput
from scandoc.providers.figures.registry import (
    FigureProviderRegistry,
    default_figure_registry,
)
from scandoc.providers.figures.remote_provider import GenericRemoteFigureProvider
from scandoc.providers.figures.taxonomy import FigureType, ProviderType

__all__ = [
    "BaseFigureProvider",
    "LocalFigureProvider",
    "HuggingFaceFigureAdapter",
    "GenericRemoteFigureProvider",
    "FigureProviderRegistry",
    "default_figure_registry",
    "FigureType",
    "ProviderType",
    "FigureConfig",
    "ImageInput",
    "FigureResult",
    "CaptionAssociator",
    "figure_result_to_document_ir",
    "FigureError",
    "FigureProviderUnavailableError",
    "PrivacyViolationError",
    "FigureInferenceError",
    "InvalidImageInputError",
]
