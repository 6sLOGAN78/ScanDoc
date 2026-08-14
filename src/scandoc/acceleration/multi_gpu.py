"""
Multi-GPU Parallelism Engine for enterprise batch document rendering and multi-device inference.
"""

from concurrent.futures import ThreadPoolExecutor
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from scandoc.acceleration.discovery import DeviceDiscovery
from scandoc.acceleration.models import DeviceContext, DeviceType, PrecisionMode

logger = logging.getLogger("scandoc.acceleration.multi_gpu")


class MultiGpuExecutionPool:
    """
    Multi-GPU Parallel Execution Pool distributing page processing tasks across multiple CUDA devices.
    """

    def __init__(
        self,
        device_indices: Optional[List[int]] = None,
        max_workers_per_gpu: int = 2,
    ):
        if device_indices is not None:
            self.device_indices = list(device_indices)
        else:
            available_count = DeviceDiscovery.get_cuda_device_count()
            self.device_indices = list(range(max(1, available_count)))

        if not self.device_indices:
            self.device_indices = [0]

        self.max_workers_per_gpu = max_workers_per_gpu
        total_workers = len(self.device_indices) * self.max_workers_per_gpu
        self._executor = ThreadPoolExecutor(max_workers=total_workers)
        self._rr_counter = 0

        logger.info(
            "MultiGpuExecutionPool initialized across GPUs %s (%d worker threads)",
            self.device_indices,
            total_workers,
        )

    def get_next_device_context(self) -> DeviceContext:
        """Return next DeviceContext in round-robin sequence."""
        gpu_idx = self.device_indices[self._rr_counter % len(self.device_indices)]
        self._rr_counter += 1

        dev_type = DeviceType.CUDA if DeviceDiscovery.is_cuda_available() else DeviceType.CPU
        return DeviceContext(
            device_type=dev_type,
            device_index=gpu_idx,
            backend="onnxruntime",
            precision=PrecisionMode.FP16,
        )

    def map_batch(self, task_fn: Callable[[Any, DeviceContext], Any], items: List[Any]) -> List[Any]:
        """
        Execute task_fn over items concurrently, binding each task execution to a assigned GPU device context.
        """
        futures = []
        for item in items:
            ctx = self.get_next_device_context()
            fut = self._executor.submit(task_fn, item, ctx)
            futures.append(fut)

        return [f.result() for f in futures]

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the multi-GPU worker thread pool."""
        self._executor.shutdown(wait=wait)
