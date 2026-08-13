"""
CPU Execution Backend implementation.
"""

import logging
import os
import time
from typing import Any, List, Optional

from scandoc.acceleration.base import BaseExecutionBackend
from scandoc.acceleration.models import (
    BackendCapability,
    DeviceContext,
    DeviceType,
    PrecisionMode,
)

logger = logging.getLogger("scandoc.acceleration.backends.cpu")


class CpuExecutionBackend(BaseExecutionBackend):
    """
    High-performance CPU Execution Backend.
    
    Configures worker thread allocation, OpenMP intra/inter-op parameters,
    and ONNX Runtime CPUExecutionProvider settings.
    """

    def __init__(self, context: Optional[DeviceContext] = None):
        self._context = context or DeviceContext(device_type=DeviceType.CPU)
        self._initialized = False

    @property
    def backend_name(self) -> str:
        return "cpu"

    @property
    def capabilities(self) -> BackendCapability:
        return BackendCapability(
            backend_name=self.backend_name,
            supported_devices=[DeviceType.CPU],
            supported_precisions=[PrecisionMode.FP32, PrecisionMode.INT8],
            supports_batching=True,
            supports_async=False,
        )

    @property
    def is_available(self) -> bool:
        return True

    def initialize(self, context: Optional[DeviceContext] = None) -> None:
        if context is not None:
            self._context = context

        num_threads = self._context.num_threads
        # Set OpenMP and ONNX thread environment variables
        os.environ["OMP_NUM_THREADS"] = str(num_threads)
        os.environ["MKL_NUM_THREADS"] = str(num_threads)

        self._initialized = True
        logger.debug("CpuExecutionBackend initialized with %d worker threads", num_threads)

    def get_onnx_session_options(self) -> Any:
        """Create configured ONNX SessionOptions for CPU execution."""
        try:
            import onnxruntime as ort  # type: ignore
            opts = ort.SessionOptions()
            opts.intra_op_num_threads = self._context.num_threads
            opts.inter_op_num_threads = max(1, self._context.num_threads // 2)
            opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            return opts
        except ImportError:
            return None

    def run_inference(self, model_session: Any, inputs: Any) -> Any:
        if not self._initialized:
            self.initialize()

        if hasattr(model_session, "run"):
            # ONNX Runtime InferenceSession
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
