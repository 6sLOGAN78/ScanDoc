"""
Process memory and RSS tracking profiler.
"""

import os
import tracemalloc
from typing import Optional


class MemoryProfiler:
    """
    Tracks process resident set size (RSS) RAM memory usage via psutil or tracemalloc fallback.
    """

    def __init__(self):
        self._has_psutil = False
        try:
            import psutil
            self._has_psutil = True
            self._process = psutil.Process(os.getpid())
        except ImportError:
            self._has_psutil = False

    def get_current_rss_mb(self) -> float:
        """Get current process resident set size in MB."""
        if self._has_psutil:
            return round(self._process.memory_info().rss / (1024 * 1024), 2)
        return 0.0

    def start_tracing(self):
        if not tracemalloc.is_tracing():
            tracemalloc.start()

    def get_traced_peak_mb(self) -> float:
        if tracemalloc.is_tracing():
            _, peak = tracemalloc.get_traced_memory()
            return round(peak / (1024 * 1024), 2)
        return 0.0
