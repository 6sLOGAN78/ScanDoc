"""
Stage timing and latency profiler for pipeline execution.
"""

import time
from typing import Dict, Optional


class StageTimer:
    """
    Context manager and dict tracker for measuring per-stage execution latency.
    """

    def __init__(self):
        self.stage_timings: Dict[str, float] = {}

    def measure(self, stage_name: str):
        """Context manager for timing a named stage."""
        return _StageTimerContext(self, stage_name)

    def record_stage(self, stage_name: str, duration_sec: float):
        """Record timing for a named stage directly."""
        self.stage_timings[stage_name] = round(duration_sec, 6)


class _StageTimerContext:

    def __init__(self, timer: StageTimer, stage_name: str):
        self.timer = timer
        self.stage_name = stage_name
        self.t0 = 0.0

    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.t0
        self.timer.record_stage(self.stage_name, elapsed)
