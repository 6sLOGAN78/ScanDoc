"""
Unified benchmark runner orchestrator.
"""

from typing import List, Optional
from scandoc.benchmarks.adapters.base import BaseBenchmarkAdapter
from scandoc.benchmarks.adapters.docling_adapter import DoclingAdapter
from scandoc.benchmarks.adapters.scandoc_adapter import ScanDocAdapter
from scandoc.benchmarks.config import BenchmarkConfig
from scandoc.benchmarks.core import BenchmarkRunner, get_environment_meta
from scandoc.benchmarks.datasets import DatasetManager
from scandoc.benchmarks.models import BenchmarkCase, BenchmarkResult


def run_benchmark_suite(
    config: Optional[BenchmarkConfig] = None,
    cases: Optional[List[BenchmarkCase]] = None,
) -> List[BenchmarkResult]:
    """
    Run full benchmark suite across scanDOC and optional Docling adapters.
    """
    cfg = config or BenchmarkConfig()
    ds_mgr = DatasetManager(manifest_path=cfg.dataset_manifest_path)
    bench_cases = cases or ds_mgr.get_benchmark_cases()

    adapters: List[BaseBenchmarkAdapter] = [ScanDocAdapter()]
    if cfg.docling_enabled:
        adapters.append(DoclingAdapter())

    runner = BenchmarkRunner(adapters=adapters)
    results = runner.run_all(bench_cases, iterations=cfg.iterations, warmup=cfg.warmup)
    return results
