"""
Vision-Language Model (VLM) Provider System for scanDOC.
"""

from scandoc.providers.vlm.adapter import VlmDocumentAdapter
from scandoc.providers.vlm.base import BaseVlmProvider
from scandoc.providers.vlm.exceptions import (
    PrivacyViolationError,
    VlmError,
    VlmInferenceError,
    VlmOutputValidationError,
    VlmProviderUnavailableError,
)
from scandoc.providers.vlm.huggingface_vlm import HuggingFaceVlmAdapter
from scandoc.providers.vlm.local_vlm import LocalVlmProvider
from scandoc.providers.vlm.models import VlmConfig, VlmRequest, VlmResult
from scandoc.providers.vlm.openai_vlm import OpenAiCompatibleVlmProvider
from scandoc.providers.vlm.registry import VlmProviderRegistry, default_vlm_registry
from scandoc.providers.vlm.remote_vlm import GenericRemoteVlmProvider
from scandoc.providers.vlm.taxonomy import ProviderType, VlmExecutionMode, VlmTaskType
from scandoc.providers.vlm.validator import VlmOutputValidator

__all__ = [
    "BaseVlmProvider",
    "LocalVlmProvider",
    "HuggingFaceVlmAdapter",
    "GenericRemoteVlmProvider",
    "OpenAiCompatibleVlmProvider",
    "VlmProviderRegistry",
    "default_vlm_registry",
    "VlmTaskType",
    "VlmExecutionMode",
    "ProviderType",
    "VlmConfig",
    "VlmRequest",
    "VlmResult",
    "VlmOutputValidator",
    "VlmDocumentAdapter",
    "VlmError",
    "VlmProviderUnavailableError",
    "PrivacyViolationError",
    "VlmInferenceError",
    "VlmOutputValidationError",
]
