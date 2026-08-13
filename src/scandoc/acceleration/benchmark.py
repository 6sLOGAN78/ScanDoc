"""
Performance benchmarking harness measuring inference latency, batch throughput, and memory footprint.
"""

import time
from typing import Any, Callable, Dict, List, Optional
import psutil
from pydantic import BaseModel, Field

from scandoc.acceleration.models import DeviceContext


class BenchmarkReport(BaseModel):
    """
    Performance benchmark report.
    """
    device_context: DeviceContext = Field(..., description="Target device context evaluated")
    num_runs: int = Field(..., ge=1, description="Number of inference repetitions executed")
    total_time_ms: float = Field(..., ge=0.0, description="Total wall-clock benchmark time in ms")
    mean_latency_ms: float = Field(..., ge=0.0, description="Mean single inference latency in ms")
    p95_latency_ms: float = Field(..., ge=0.0, description="95th percentile latency in ms")
    throughput_fps: float = Field(..., ge=0.0, description="Inference throughput in items/second")
    ram_usage_mb: float = Field(..., ge=0.0, description="Resident Set Size (RSS) RAM usage in MB")
    environment_info: Dict[str, str] = Field(default_factory=dict, description="Hardware and software environment tags")


class BenchmarkRunner:
    """
    Harness executing hardware benchmarks over model functions and batch inputs.
    """

    @classmethod
    def run_benchmark(
        cls,
        inference_fn: Callable[[Any], Any],
        sample_input: Any,
        device_context: DeviceContext,
        num_runs: int = 10,
        warmup_runs: int = 2,
    ) -> BenchmarkReport:
        """
        Execute benchmark over an inference function.
        """
        # Warmup runs
        for _ in range(warmup_runs):
            _ = inference_fn(sample_input)

        latencies: List[float] = []

        # Timed benchmark loop
        start_total = time.perf_counter()
        for _ in range(num_runs):
            t0 = time.perf_counter()
            _ = inference_fn(sample_input)
            latencies.append((time.perf_counter() - t0) * 1000.0)

        total_time_ms = (time.perf_counter() - start_total) * 1000.0
        mean_latency = float(sum(latencies) / len(latencies))

        sorted_lat = sorted(latencies)
        p95_idx = int(0.95 * len(sorted_lat))
        p95_latency = sorted_lat[min(p95_idx, len(sorted_lat) - 1)]

        throughput = (num_runs / (total_time_ms / 1000.0)) if total_time_ms > 0 else 0.0

        # Memory footprint
        process = psutil.Process()
        ram_mb = process.memory_info().rss / (1024 * 1024)

        return BenchmarkReport(
            device_context=device_context,
            num_runs=num_runs,
            total_time_ms=round(total_time_ms, 2),
            mean_latency_ms=round(mean_latency, 2),
            p95_latency_ms=round(p95_latency, 2),
            throughput_fps=round(throughput, 2),
            ram_usage_mb=round(ram_mb, 2),
            environment_info={
                "backend": device_context.backend,
                "device": device_context.to_device_string(),
                "precision": device_context.precision.value,
            },
        )
