"""
Worker pool executor managing thread concurrency, bounded backpressure queues, and cancellation signals.
"""

from concurrent.futures import ThreadPoolExecutor, Future
import logging
import threading
import time
from typing import Callable, List, Optional, TypeVar

from scandoc.pipelines.exceptions import (
    PipelineCancelledError,
    PipelineTimeoutError,
    QueueOverflowError,
    WorkerExecutionError,
)
from scandoc.pipelines.models import PipelineConfig

logger = logging.getLogger("scandoc.pipelines.executor")

T = TypeVar("T")


class PipelineThreadPool:
    """
    Worker pool maintaining thread concurrency, backpressure semaphores, and cancellation events.
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self._executor = ThreadPoolExecutor(
            max_workers=config.max_workers,
            thread_name_prefix="scandoc_worker",
        )
        self._semaphore = threading.Semaphore(config.queue_size)
        self._cancel_event = threading.Event()
        self._lock = threading.Lock()

    @property
    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    def cancel(self) -> None:
        """Signal cancellation to all active worker tasks."""
        self._cancel_event.set()

    def submit_task(self, func: Callable[..., T], *args, **kwargs) -> Future[T]:
        """
        Submit task to worker pool, applying backpressure via queue semaphore.
        """
        if self._cancel_event.is_set():
            raise PipelineCancelledError("Pipeline execution has been cancelled.")

        # Acquire semaphore for bounded backpressure
        acquired = self._semaphore.acquire(timeout=self.config.timeout_seconds)
        if not acquired:
            raise QueueOverflowError(f"Worker queue backpressure limit ({self.config.queue_size}) exceeded.")

        def wrapper() -> T:
            try:
                if self._cancel_event.is_set():
                    raise PipelineCancelledError("Task cancelled before execution.")
                
                # Execute with transient retry policy
                attempts = 0
                while True:
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        attempts += 1
                        if attempts > self.config.max_retries:
                            raise WorkerExecutionError(f"Task failed after {attempts} attempts: {e}") from e
                        time.sleep(0.01 * (2 ** attempts))
            finally:
                self._semaphore.release()

        return self._executor.submit(wrapper)

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown worker thread pool."""
        self._executor.shutdown(wait=wait, cancel_futures=True)
