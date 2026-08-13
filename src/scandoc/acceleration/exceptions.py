"""
Exception classes for hardware execution engine.
"""


class ExecutionEngineError(Exception):
    """Base exception for hardware execution engine errors."""
    pass


class DeviceNotFoundError(ExecutionEngineError):
    """Raised when a requested hardware device (e.g. cuda:0) cannot be found."""
    pass


class BackendUnavailableError(ExecutionEngineError):
    """Raised when a requested execution backend (e.g. OpenVINO, TensorRT) is not installed."""
    pass


class InferenceExecutionError(ExecutionEngineError):
    """Raised when model inference execution fails."""
    pass


class PrecisionUnsupportedError(ExecutionEngineError):
    """Raised when requested precision (e.g. INT8, FP16) is unsupported by hardware/backend."""
    pass
