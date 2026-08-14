"""
Benchmark profiling and telemetry subsystem.
"""

from scandoc.benchmarks.profiling.cpu import get_cpu_telemetry
from scandoc.benchmarks.profiling.gpu import get_gpu_telemetry
from scandoc.benchmarks.profiling.latency import StageTimer
from scandoc.benchmarks.profiling.memory import MemoryProfiler

__all__ = [
    "StageTimer",
    "MemoryProfiler",
    "get_cpu_telemetry",
    "get_gpu_telemetry",
]
