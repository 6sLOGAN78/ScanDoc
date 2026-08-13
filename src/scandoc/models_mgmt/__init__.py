"""
Model Management & Local Model Runtime Subsystem for scanDOC.
"""

from scandoc.models_mgmt.downloader import ModelDownloader
from scandoc.models_mgmt.exceptions import (
    InsufficientDiskSpaceError,
    ModelDownloadError,
    ModelLoadError,
    ModelManagementError,
    ModelNotFoundError,
    ModelValidationError,
    OfflineModeError,
)
from scandoc.models_mgmt.loader import (
    BaseModelLoader,
    DefaultOnnxModelLoader,
    LoadedModelCache,
)
from scandoc.models_mgmt.manager import ModelManager, default_model_manager
from scandoc.models_mgmt.models import ModelSpec, ValidationResult
from scandoc.models_mgmt.registry import ModelRegistry, default_model_registry
from scandoc.models_mgmt.store import DEFAULT_MODEL_DIR, ModelStore
from scandoc.models_mgmt.taxonomy import (
    ModelFormat,
    ModelSource,
    ModelState,
    QuantizationType,
    TaskType,
)
from scandoc.models_mgmt.validator import ModelValidator

__all__ = [
    "ModelSpec",
    "ValidationResult",
    "ModelStore",
    "ModelRegistry",
    "default_model_registry",
    "ModelDownloader",
    "ModelValidator",
    "BaseModelLoader",
    "DefaultOnnxModelLoader",
    "LoadedModelCache",
    "ModelManager",
    "default_model_manager",
    "DEFAULT_MODEL_DIR",
    "TaskType",
    "ModelSource",
    "ModelFormat",
    "ModelState",
    "QuantizationType",
    "ModelManagementError",
    "ModelNotFoundError",
    "ModelDownloadError",
    "ModelValidationError",
    "OfflineModeError",
    "InsufficientDiskSpaceError",
    "ModelLoadError",
]
