"""
Abstract Base Class contract for all hardware execution backends.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from scandoc.acceleration.models import BackendCapability, DeviceContext


class BaseExecutionBackend(ABC):
    """
    Abstract Base Class for hardware execution backends (CPU, CUDA, OpenVINO, TensorRT).
    """

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Return unique backend identifier."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> BackendCapability:
        """Return declared capabilities for this backend."""
        pass

    @property
    def is_available(self) -> bool:
        """Return True if backend dependencies and drivers are available."""
        return True

    @abstractmethod
    def initialize(self, context: Optional[DeviceContext] = None) -> None:
        """Initialize backend resources for target DeviceContext."""
        pass

    @abstractmethod
    def run_inference(self, model_session: Any, inputs: Any) -> Any:
        """
        Execute model inference on hardware device.
        """
        pass

    def run_batch_inference(self, model_session: Any, inputs_batch: List[Any]) -> List[Any]:
        """
        Execute batch inference on hardware device.
        """
        return [self.run_inference(model_session, item) for item in inputs_batch]

    def shutdown(self) -> None:
        """Release allocated device handles or memory buffers."""
        pass

    def __enter__(self) -> "BaseExecutionBackend":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown()
