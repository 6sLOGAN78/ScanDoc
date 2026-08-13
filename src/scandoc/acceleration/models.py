"""
Enums and Pydantic models for hardware devices, precision modes, and execution context.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DeviceType(str, Enum):
    CPU = "cpu"
    CUDA = "cuda"
    OPENVINO = "openvino"
    TENSORRT = "tensorrt"
    MPS = "mps"
    NPU = "npu"


class PrecisionMode(str, Enum):
    FP32 = "fp32"
    FP16 = "fp16"
    INT8 = "int8"


class BatchMode(str, Enum):
    SINGLE = "single"
    FIXED = "fixed"
    DYNAMIC = "dynamic"


class DeviceContext(BaseModel):
    """
    Hardware execution context representation.
    """
    device_type: DeviceType = Field(DeviceType.CPU, description="Hardware device category")
    device_index: int = Field(0, ge=0, description="Device ordinal index (e.g. 0 for cuda:0)")
    backend: str = Field("onnxruntime", description="Execution runtime backend name")
    precision: PrecisionMode = Field(PrecisionMode.FP32, description="Model inference precision mode")
    num_threads: int = Field(4, ge=1, description="CPU worker thread allocation")
    memory_limit_mb: Optional[int] = Field(None, ge=1, description="Optional memory allocation cap in MB")
    extra_options: Dict[str, str] = Field(default_factory=dict, description="Backend-specific options")

    def to_device_string(self) -> str:
        """Return standardized device string (e.g. 'cpu', 'cuda:0', 'openvino:cpu')."""
        if self.device_type == DeviceType.CUDA:
            return f"cuda:{self.device_index}"
        elif self.device_type == DeviceType.OPENVINO:
            return f"openvino:{self.device_index}"
        return self.device_type.value


class BackendCapability(BaseModel):
    """
    Metadata declaring capabilities supported by a specific execution backend.
    """
    backend_name: str = Field(..., description="Unique backend name")
    supported_devices: List[DeviceType] = Field(default_factory=list, description="Supported hardware devices")
    supported_precisions: List[PrecisionMode] = Field(default_factory=list, description="Supported precisions")
    supports_batching: bool = Field(True, description="True if supports batch inference")
    supports_async: bool = Field(False, description="True if supports asynchronous execution")
