"""
Hardware execution backend implementations for scanDOC.
"""

from scandoc.acceleration.backends.cpu_backend import CpuExecutionBackend
from scandoc.acceleration.backends.cuda_backend import CudaExecutionBackend
from scandoc.acceleration.backends.openvino_backend import OpenVinoExecutionBackend
from scandoc.acceleration.backends.tensorrt_backend import TensorRtExecutionBackend

__all__ = [
    "CpuExecutionBackend",
    "CudaExecutionBackend",
    "OpenVinoExecutionBackend",
    "TensorRtExecutionBackend",
]
