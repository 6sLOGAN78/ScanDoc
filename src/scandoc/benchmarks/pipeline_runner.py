"""
Per-stage scanDOC pipeline benchmark runner.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import time

from scandoc.benchmarks.adapters.scandoc_adapter import ScanDocAdapter
from scandoc.benchmarks.models import BenchmarkConversionResult
from scandoc.benchmarks.profiling.latency import StageTimer
from scandoc.pipelines import PipelineConfig


class ScanDocBenchmarkPipelineRunner:
    """
    Executes scanDOC document pipeline with per-stage timing profiler breakdown.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.adapter = ScanDocAdapter(config=config)

    def run_benchmark(self, file_path: str) -> Dict[str, Any]:
        timer = StageTimer()

        with timer.measure("total_pipeline"):
            conv_res = self.adapter.convert(file_path)

        return {
            "conversion": conv_res,
            "stage_timings": timer.stage_timings,
        }
