"""
CUDA GPU Execution Backend implementation with graceful CPU fallback.
"""

import logging
from typing import Any, List, Optional

from scandoc.acceleration.base import BaseExecutionBackend
from scandoc.acceleration.discovery import DeviceDiscovery
from scandoc.acceleration.exceptions import BackendUnavailableError
from scandoc.acceleration.models import (
    BackendCapability,
    DeviceContext,
    DeviceType,
    PrecisionMode,
)

logger = logging.getLogger("scandoc.acceleration.backends.cuda")


class CudaExecutionBackend(BaseExecutionBackend):
    """
    CUDA GPU Execution Backend.
    
    Provides CUDA hardware acceleration via ONNX Runtime CUDAExecutionProvider or PyTorch.
    Falls back gracefully if CUDA hardware is not detected.
    """

    def __init__(self, context: Optional[DeviceContext] = None):
        self._context = context or DeviceContext(device_type=DeviceType.CUDA)
        self._initialized = False

    @property
    def backend_name(self) -> str:
        return "cuda"

    @property
    def capabilities(self) -> BackendCapability:
        return BackendCapability(
            backend_name=self.backend_name,
            supported_devices=[DeviceType.CUDA],
            supported_precisions=[PrecisionMode.FP32, PrecisionMode.FP16, PrecisionMode.INT8],
            supports_batching=True,
            supports_async=True,
        )

    @property
    def is_available(self) -> bool:
        return DeviceDiscovery.is_cuda_available()

    def initialize(self, context: Optional[DeviceContext] = None) -> None:
        if context is not None:
            self._context = context

        if not self.is_available:
            raise BackendUnavailableError(
                "CUDA execution backend is not available. Install CUDA drivers and onnxruntime-gpu/torch with CUDA support."
            )

        self._initialized = True
        logger.info("CudaExecutionBackend initialized for device index cuda:%d", self._context.device_index)

    def get_onnx_execution_providers(self) -> List[Any]:
        """Return provider configuration tuple list for ONNX Runtime."""
        return [
            (
                "CUDAExecutionProvider",
                {
                    "device_id": self._context.device_index,
                    "arena_extend_strategy": "kNextPowerOfTwo",
                    "gpu_mem_limit": (self._context.memory_limit_mb * 1024 * 1024) if self._context.memory_limit_mb else 0,
                },
            ),
            "CPUExecutionProvider",
        ]

    def run_inference(self, model_session: Any, inputs: Any) -> Any:
        if not self._initialized:
            self.initialize()

        if hasattr(model_session, "run"):
            input_names = [inp.name for inp in model_session.get_inputs()]
            if isinstance(inputs, dict):
                feed_dict = inputs
            elif isinstance(inputs, (list, tuple)):
                feed_dict = {name: val for name, val in zip(input_names, inputs)}
            else:
                feed_dict = {input_names[0]: inputs}
            return model_session.run(None, feed_dict)
        elif callable(model_session):
            return model_session(inputs)

        return inputs
