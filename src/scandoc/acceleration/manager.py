"""
Central ExecutionManager managing session pools, device selection, and backend orchestration.
"""

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from scandoc.acceleration.backends import (
    CpuExecutionBackend,
    CudaExecutionBackend,
    OpenVinoExecutionBackend,
    TensorRtExecutionBackend,
)
from scandoc.acceleration.base import BaseExecutionBackend
from scandoc.acceleration.discovery import DeviceDiscovery
from scandoc.acceleration.exceptions import BackendUnavailableError, DeviceNotFoundError
from scandoc.acceleration.models import DeviceContext, DeviceType, PrecisionMode
from scandoc.acceleration.multi_gpu import MultiGpuExecutionPool
from scandoc.acceleration.quantization import ModelQuantizer, QuantizationConfig

logger = logging.getLogger("scandoc.acceleration.manager")


class ExecutionManager:
    """
    Orchestrates hardware devices, session pools, quantization, and backend selection.
    """

    def __init__(self, register_defaults: bool = True):
        self._backends: Dict[str, BaseExecutionBackend] = {}
        self._session_pool: Dict[str, Any] = {}
        if register_defaults:
            self._register_default_backends()

    def _register_default_backends(self) -> None:
        defaults = [
            CpuExecutionBackend(),
            CudaExecutionBackend(),
            OpenVinoExecutionBackend(),
            TensorRtExecutionBackend(),
        ]
        for b in defaults:
            self.register_backend(b)

    def register_backend(self, backend: BaseExecutionBackend) -> None:
        """Register an execution backend."""
        self._backends[backend.backend_name.lower()] = backend

    def get_backend(self, backend_name: str) -> BaseExecutionBackend:
        """Get registered backend instance by name."""
        bname = backend_name.lower()
        if bname not in self._backends:
            raise BackendUnavailableError(f"Execution backend '{backend_name}' is not registered.")
        return self._backends[bname]

    def list_backends(self) -> List[BaseExecutionBackend]:
        """Return list of all registered execution backends."""
        return list(self._backends.values())

    def select_device(self, requested_device: str = "auto") -> DeviceContext:
        """
        Deterministically select an available DeviceContext based on hardware discovery and requested strategy.
        """
        req_clean = requested_device.lower().strip()

        # Explicit CPU request
        if req_clean == "cpu":
            return DeviceContext(device_type=DeviceType.CPU, backend="onnxruntime")

        # Explicit TensorRT request
        if req_clean.startswith("tensorrt"):
            if DeviceDiscovery.is_tensorrt_available():
                return DeviceContext(device_type=DeviceType.TENSORRT, device_index=0, backend="tensorrt", precision=PrecisionMode.FP16)
            elif DeviceDiscovery.is_cuda_available():
                logger.warning("TensorRT runtime unavailable. Falling back to CUDA GPU execution.")
                return DeviceContext(device_type=DeviceType.CUDA, device_index=0, backend="onnxruntime", precision=PrecisionMode.FP16)
            logger.warning("Requested TensorRT device unavailable. Falling back to CPU.")
            return DeviceContext(device_type=DeviceType.CPU, backend="onnxruntime")

        # Explicit CUDA request
        if req_clean.startswith("cuda"):
            if DeviceDiscovery.is_cuda_available():
                idx = 0
                if ":" in req_clean:
                    try:
                        idx = int(req_clean.split(":")[1])
                    except ValueError:
                        idx = 0
                return DeviceContext(device_type=DeviceType.CUDA, device_index=idx, backend="onnxruntime", precision=PrecisionMode.FP16)
            logger.warning("Requested device '%s' unavailable. Falling back to CPU.", requested_device)
            return DeviceContext(device_type=DeviceType.CPU, backend="onnxruntime")

        # Explicit OpenVINO request
        if req_clean.startswith("openvino"):
            if DeviceDiscovery.is_openvino_available():
                return DeviceContext(device_type=DeviceType.OPENVINO, backend="openvino")
            logger.warning("Requested OpenVINO device unavailable. Falling back to CPU.")
            return DeviceContext(device_type=DeviceType.CPU, backend="onnxruntime")

        # Auto Selection Priority: TensorRT -> CUDA -> OpenVINO -> CPU
        if DeviceDiscovery.is_tensorrt_available():
            return DeviceContext(device_type=DeviceType.TENSORRT, device_index=0, backend="tensorrt", precision=PrecisionMode.FP16)

        if DeviceDiscovery.is_cuda_available():
            return DeviceContext(device_type=DeviceType.CUDA, device_index=0, backend="onnxruntime", precision=PrecisionMode.FP16)

        if DeviceDiscovery.is_openvino_available():
            return DeviceContext(device_type=DeviceType.OPENVINO, backend="openvino")

        # Default CPU fallback
        return DeviceContext(device_type=DeviceType.CPU, backend="onnxruntime")

    def get_onnx_execution_providers(self, context: Optional[DeviceContext] = None) -> List[str]:
        """
        Return list of ONNX Runtime execution provider names ordered by hardware priority.
        """
        ctx = context or self.select_device("auto")
        providers = []

        if ctx.device_type == DeviceType.TENSORRT and DeviceDiscovery.is_tensorrt_available():
            providers.extend(["TensorRTExecutionProvider", "CUDAExecutionProvider"])
        elif ctx.device_type == DeviceType.CUDA and DeviceDiscovery.is_cuda_available():
            providers.append("CUDAExecutionProvider")
        elif ctx.device_type == DeviceType.OPENVINO and DeviceDiscovery.is_openvino_available():
            providers.append("OpenVINOExecutionProvider")

        providers.append("CPUExecutionProvider")
        return providers

    def create_multi_gpu_pool(self, device_indices: Optional[List[int]] = None) -> MultiGpuExecutionPool:
        """Create a MultiGpuExecutionPool for batch parallel document processing."""
        return MultiGpuExecutionPool(device_indices=device_indices)

    def quantize_model(
        self,
        model_path: Union[str, Path],
        precision: PrecisionMode = PrecisionMode.FP16,
    ) -> Path:
        """Quantize model file to FP16 or INT8 precision."""
        return ModelQuantizer.quantize_onnx_model(model_path, config=QuantizationConfig(precision=precision))

    def get_or_create_session(self, session_key: str, create_fn: Callable[[], Any]) -> Any:
        """
        Reuse or create an expensive model session to avoid repeated initialization and memory copies.
        """
        if session_key in self._session_pool:
            return self._session_pool[session_key]

        logger.debug("Creating new session for model key '%s'", session_key)
        session = create_fn()
        self._session_pool[session_key] = session
        return session

    def clear_session_pool(self) -> None:
        """Clear all cached model sessions."""
        self._session_pool.clear()


# Default Global Execution Manager Singleton
default_execution_manager = ExecutionManager()
