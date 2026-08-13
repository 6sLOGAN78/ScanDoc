"""
Hardware environment discovery engine inspecting CPU, CUDA, OpenVINO, TensorRT, and MPS.
"""

import logging
import os
import psutil
from typing import Dict, List

from scandoc.acceleration.models import DeviceContext, DeviceType, PrecisionMode

logger = logging.getLogger("scandoc.acceleration.discovery")


class DeviceDiscovery:
    """
    Discovers available execution runtimes and hardware devices.
    """

    @classmethod
    def discover_devices(cls) -> List[DeviceContext]:
        """
        Scan system environment and return list of verified available DeviceContexts.
        """
        available: List[DeviceContext] = []

        # 1. CPU is always available
        num_cores = os.cpu_count() or 4
        available.append(
            DeviceContext(
                device_type=DeviceType.CPU,
                device_index=0,
                backend="onnxruntime",
                precision=PrecisionMode.FP32,
                num_threads=min(num_cores, 8),
            )
        )

        # 2. Check CUDA GPU
        if cls.is_cuda_available():
            cuda_count = cls.get_cuda_device_count()
            for idx in range(cuda_count):
                available.append(
                    DeviceContext(
                        device_type=DeviceType.CUDA,
                        device_index=idx,
                        backend="onnxruntime",
                        precision=PrecisionMode.FP16,
                    )
                )

        # 3. Check OpenVINO
        if cls.is_openvino_available():
            available.append(
                DeviceContext(
                    device_type=DeviceType.OPENVINO,
                    device_index=0,
                    backend="openvino",
                    precision=PrecisionMode.FP32,
                )
            )

        # 4. Check TensorRT
        if cls.is_tensorrt_available():
            available.append(
                DeviceContext(
                    device_type=DeviceType.TENSORRT,
                    device_index=0,
                    backend="tensorrt",
                    precision=PrecisionMode.FP16,
                )
            )

        # 5. Check Apple MPS
        if cls.is_mps_available():
            available.append(
                DeviceContext(
                    device_type=DeviceType.MPS,
                    device_index=0,
                    backend="torch",
                    precision=PrecisionMode.FP32,
                )
            )

        logger.debug("Discovered %d hardware execution contexts", len(available))
        return available

    @classmethod
    def is_cuda_available(cls) -> bool:
        """Return True if CUDA GPU hardware and drivers are verified available."""
        try:
            import torch  # type: ignore
            if torch.cuda.is_available() and torch.cuda.device_count() > 0:
                return True
        except ImportError:
            pass

        try:
            import onnxruntime as ort  # type: ignore
            if "CUDAExecutionProvider" in ort.get_available_providers():
                return True
        except ImportError:
            pass

        return False

    @classmethod
    def get_cuda_device_count(cls) -> int:
        """Return number of available CUDA GPUs."""
        try:
            import torch  # type: ignore
            if torch.cuda.is_available():
                return torch.cuda.device_count()
        except ImportError:
            pass
        return 1 if cls.is_cuda_available() else 0

    @classmethod
    def is_openvino_available(cls) -> bool:
        """Return True if OpenVINO runtime is available."""
        try:
            import openvino  # type: ignore
            return True
        except ImportError:
            pass

        try:
            import onnxruntime as ort  # type: ignore
            if "OpenVINOExecutionProvider" in ort.get_available_providers():
                return True
        except ImportError:
            pass

        return False

    @classmethod
    def is_tensorrt_available(cls) -> bool:
        """Return True if TensorRT runtime is available."""
        try:
            import onnxruntime as ort  # type: ignore
            if "TensorRTExecutionProvider" in ort.get_available_providers():
                return True
        except ImportError:
            pass
        return False

    @classmethod
    def is_mps_available(cls) -> bool:
        """Return True if Apple Metal Performance Shaders (MPS) is available."""
        try:
            import torch  # type: ignore
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return True
        except ImportError:
            pass
        return False

    @classmethod
    def get_system_memory_mb(cls) -> int:
        """Return total system RAM in MB."""
        try:
            return int(psutil.virtual_memory().total / (1024 * 1024))
        except Exception:
            return 8192
