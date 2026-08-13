"""
Hardware Execution & Acceleration Engine for scanDOC.
"""

from scandoc.acceleration.backends import (
    CpuExecutionBackend,
    CudaExecutionBackend,
    OpenVinoExecutionBackend,
    TensorRtExecutionBackend,
)
from scandoc.acceleration.base import BaseExecutionBackend
from scandoc.acceleration.benchmark import BenchmarkReport, BenchmarkRunner
from scandoc.acceleration.discovery import DeviceDiscovery
from scandoc.acceleration.exceptions import (
    BackendUnavailableError,
    DeviceNotFoundError,
    ExecutionEngineError,
    InferenceExecutionError,
    PrecisionUnsupportedError,
)
from scandoc.acceleration.manager import ExecutionManager, default_execution_manager
from scandoc.acceleration.models import (
    BackendCapability,
    BatchMode,
    DeviceContext,
    DeviceType,
    PrecisionMode,
)

__all__ = [
    "DeviceType",
    "PrecisionMode",
    "BatchMode",
    "DeviceContext",
    "BackendCapability",
    "DeviceDiscovery",
    "BaseExecutionBackend",
    "CpuExecutionBackend",
    "CudaExecutionBackend",
    "OpenVinoExecutionBackend",
    "TensorRtExecutionBackend",
    "ExecutionManager",
    "default_execution_manager",
    "BenchmarkRunner",
    "BenchmarkReport",
    "ExecutionEngineError",
    "DeviceNotFoundError",
    "BackendUnavailableError",
    "InferenceExecutionError",
    "PrecisionUnsupportedError",
]
