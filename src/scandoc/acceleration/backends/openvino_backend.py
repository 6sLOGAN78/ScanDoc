"""
OpenVINO Execution Backend implementation.
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

logger = logging.getLogger("scandoc.acceleration.backends.openvino")


class OpenVinoExecutionBackend(BaseExecutionBackend):
    """
    OpenVINO Execution Backend.
    """

    def __init__(self, context: Optional[DeviceContext] = None):
        self._context = context or DeviceContext(device_type=DeviceType.OPENVINO)
        self._initialized = False

    @property
    def backend_name(self) -> str:
        return "openvino"

    @property
    def capabilities(self) -> BackendCapability:
        return BackendCapability(
            backend_name=self.backend_name,
            supported_devices=[DeviceType.OPENVINO, DeviceType.CPU, DeviceType.NPU],
            supported_precisions=[PrecisionMode.FP32, PrecisionMode.FP16, PrecisionMode.INT8],
            supports_batching=True,
            supports_async=True,
        )

    @property
    def is_available(self) -> bool:
        return DeviceDiscovery.is_openvino_available()

    def initialize(self, context: Optional[DeviceContext] = None) -> None:
        if context is not None:
            self._context = context

        if not self.is_available:
            raise BackendUnavailableError(
                "OpenVINO execution backend is not available. Install openvino or onnxruntime OpenVINOExecutionProvider."
            )
        self._initialized = True
        logger.info("OpenVinoExecutionBackend initialized successfully")

    def run_inference(self, model_session: Any, inputs: Any) -> Any:
        if not self._initialized:
            self.initialize()

        if hasattr(model_session, "run"):
            input_names = [inp.name for inp in model_session.get_inputs()]
            if isinstance(inputs, dict):
                feed_dict = inputs
            else:
                feed_dict = {input_names[0]: inputs}
            return model_session.run(None, feed_dict)
        elif callable(model_session):
            return model_session(inputs)

        return inputs
