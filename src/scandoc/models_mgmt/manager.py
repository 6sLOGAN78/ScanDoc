"""
Unified ModelManager orchestrating discovery, acquisition, validation, loading, caching, and lifecycle management.
"""

import logging
from typing import Any, List, Optional

from scandoc.models_mgmt.downloader import ModelDownloader
from scandoc.models_mgmt.exceptions import (
    ModelLoadError,
    ModelNotFoundError,
    ModelValidationError,
)
from scandoc.models_mgmt.loader import (
    BaseModelLoader,
    DefaultOnnxModelLoader,
    LoadedModelCache,
)
from scandoc.models_mgmt.models import ModelSpec, ValidationResult
from scandoc.models_mgmt.registry import ModelRegistry, default_model_registry
from scandoc.models_mgmt.store import ModelStore
from scandoc.models_mgmt.taxonomy import ModelState, TaskType
from scandoc.models_mgmt.validator import ModelValidator

logger = logging.getLogger("scandoc.models_mgmt.manager")


class ModelManager:
    """
    Central Model Management orchestrator.
    Manages discovery, caching, acquisition, validation, loading, and hardware compatibility.
    Does NOT perform document processing.
    """

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        store: Optional[ModelStore] = None,
        offline: bool = False,
    ):
        self._registry = registry or default_model_registry
        self._store = store or ModelStore()
        self._downloader = ModelDownloader(self._store, offline=offline)
        self._cache = LoadedModelCache()
        self._loaders: List[BaseModelLoader] = [DefaultOnnxModelLoader()]

    @property
    def offline(self) -> bool:
        return self._downloader.offline

    @offline.setter
    def offline(self, value: bool) -> None:
        self._downloader.offline = value

    @property
    def store(self) -> ModelStore:
        return self._store

    @property
    def registry(self) -> ModelRegistry:
        return self._registry

    def register_loader(self, loader: BaseModelLoader) -> None:
        """Register a custom model loader."""
        self._loaders.insert(0, loader)

    def list_available_models(self, task: Optional[TaskType] = None) -> List[ModelSpec]:
        """List registered and installed models."""
        return self._registry.list_models(task=task)

    def resolve(self, model_id: str, auth_token: Optional[str] = None) -> ModelSpec:
        """
        Resolve a model specification to a verified local installation.
        Downloads artifact if missing and offline=False.
        """
        spec = self._registry.lookup(model_id) or self._store.get_model_spec(model_id)
        if not spec:
            raise ModelNotFoundError(f"Model '{model_id}' is not registered in ModelRegistry or ModelStore.")

        # Check if already installed locally
        if spec.local_path and self._store.get_model_spec(model_id):
            validation = ModelValidator.validate(spec, self._store)
            if validation.is_valid:
                self._registry.update_state(model_id, ModelState.READY)
                return spec

        # Acquire via ModelDownloader
        self._registry.update_state(model_id, ModelState.DOWNLOADING)
        installed_spec = self._downloader.download_model(spec, auth_token=auth_token)

        # Validate installation
        self._registry.update_state(model_id, ModelState.VERIFYING)
        val_res = ModelValidator.validate(installed_spec, self._store)
        if not val_res.is_valid:
            self._registry.update_state(model_id, ModelState.CORRUPTED)
            raise ModelValidationError(f"Validation failed for model '{model_id}': {val_res.errors}")

        self._registry.register(installed_spec)
        self._registry.update_state(model_id, ModelState.READY)
        return installed_spec

    def load_model(self, model_id: str, device: str = "auto") -> Any:
        """
        Load model session into memory using LoadedModelCache.
        """
        # Check cache
        cached = self._cache.get(model_id)
        if cached is not None:
            return cached

        spec = self.resolve(model_id)

        # Select appropriate loader
        loader = next((l for l in self._loaders if l.can_load(spec)), None)
        if not loader:
            raise ModelLoadError(f"No suitable model loader found for format '{spec.format.value}'.")

        self._registry.update_state(model_id, ModelState.LOADING)
        session = loader.load(spec, device=device)
        self._cache.put(model_id, session, memory_bytes=loader.inspect_memory(session))
        self._registry.update_state(model_id, ModelState.LOADED)
        return session

    def unload_model(self, model_id: str) -> None:
        """Unload model session from memory."""
        self._cache.evict(model_id)
        if self._registry.lookup(model_id):
            self._registry.update_state(model_id, ModelState.READY)


# Global Singleton
default_model_manager = ModelManager()
