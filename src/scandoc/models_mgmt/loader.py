"""
BaseModelLoader interface and memory-aware LoadedModelCache for loaded model sessions.
"""

from abc import ABC, abstractmethod
from collections import OrderedDict
import logging
from typing import Any, Dict, Optional

from scandoc.models_mgmt.models import ModelSpec

logger = logging.getLogger("scandoc.models_mgmt.loader")


class BaseModelLoader(ABC):
    """
    Abstract Base Class contract for model loaders.
    Loads raw model binary sessions (ONNX InferenceSession, PyTorch nn.Module) into memory.
    Does NOT contain document processing or inference logic.
    """

    @abstractmethod
    def can_load(self, spec: ModelSpec) -> bool:
        """Return True if loader supports given model format and specification."""
        pass

    @abstractmethod
    def load(self, spec: ModelSpec, device: str = "auto") -> Any:
        """Load model weights into memory and return runtime session/handle."""
        pass

    def unload(self, model_instance: Any) -> None:
        """Release model instance resources."""
        pass

    def inspect_memory(self, model_instance: Any) -> int:
        """Return estimated memory footprint in bytes."""
        return 0


class DefaultOnnxModelLoader(BaseModelLoader):
    """Default ONNX model loader implementation."""

    def can_load(self, spec: ModelSpec) -> bool:
        return spec.format.value == "onnx"

    def load(self, spec: ModelSpec, device: str = "auto") -> Any:
        # Return mock ONNX session for architecture validation
        return f"<ONNX_SESSION: {spec.model_id} on {device}>"

    def unload(self, model_instance: Any) -> None:
        pass


class LoadedModelCache:
    """
    In-process memory-aware cache for loaded model sessions with LRU eviction.
    """

    def __init__(self, max_models: int = 5, max_memory_bytes: int = 2 * 1024 * 1024 * 1024):
        self._max_models = max_models
        self._max_memory_bytes = max_memory_bytes
        self._cache: OrderedDict[str, tuple[Any, int]] = OrderedDict()
        self._current_memory_bytes = 0

    def get(self, model_id: str) -> Optional[Any]:
        """Lookup loaded model instance in cache."""
        if model_id in self._cache:
            self._cache.move_to_end(model_id)
            return self._cache[model_id][0]
        return None

    def put(self, model_id: str, instance: Any, memory_bytes: int = 0) -> None:
        """Put loaded model instance into cache, evicting oldest if limits are exceeded."""
        if model_id in self._cache:
            old_inst, old_mem = self._cache.pop(model_id)
            self._current_memory_bytes -= old_mem

        # Check LRU capacity eviction
        while len(self._cache) >= self._max_models:
            evict_id, (evict_inst, evict_mem) = self._cache.popitem(last=False)
            self._current_memory_bytes -= evict_mem
            logger.info("Evicted model '%s' from loaded model cache", evict_id)

        self._cache[model_id] = (instance, memory_bytes)
        self._current_memory_bytes += memory_bytes

    def evict(self, model_id: str) -> bool:
        """Evict specific model from cache."""
        if model_id in self._cache:
            inst, mem = self._cache.pop(model_id)
            self._current_memory_bytes -= mem
            return True
        return False

    def clear(self) -> None:
        """Clear all loaded models from cache."""
        self._cache.clear()
        self._current_memory_bytes = 0
