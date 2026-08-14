"""
scandoc benchmark subcommand implementation.
"""

import json
import sys
import time
from typing import Any, Dict, List

from scandoc.benchmarks import (
    BenchmarkDatasetManager,
    BenchmarkReportGenerator,
    BenchmarkRunner,
    DoclingAdapter,
    ScanDocAdapter,
)
from scandoc.cli.formatter import TerminalFormatter
from scandoc.cli.taxonomy import ExitCode
from scandoc.pipelines import DocumentPipeline, PipelineConfig, OrderingMode


def run_benchmark(args: Any) -> int:
    """
    Execute `scandoc benchmark` subcommand.
    
    Returns:
        int: Exit code (ExitCode.SUCCESS, etc.)
    """
    impl = getattr(args, "implementation", "scandoc").lower()
    dataset_path = getattr(args, "dataset", None)
    iterations = getattr(args, "iterations", 5)
    warmup = getattr(args, "warmup", 1)
    compare = getattr(args, "compare", False)

    # 1. Advanced Comparative / Adapter Benchmarking
    if dataset_path or impl in ["docling", "both", "all"] or compare:
        adapters = []
        if impl in ["scandoc", "both", "all"]:
            adapters.append(ScanDocAdapter())
        if impl in ["docling", "both", "all"]:
            adapters.append(DoclingAdapter())

        if not adapters:
            adapters = [ScanDocAdapter()]

        dataset_mgr = BenchmarkDatasetManager(dataset_path=dataset_path)
        cases = dataset_mgr.get_cases()

        runner = BenchmarkRunner(adapters=adapters)
        results = runner.run_all(cases, iterations=iterations, warmup=warmup)
        dataset_mgr.cleanup()

        if getattr(args, "json", False):
            print(BenchmarkReportGenerator.to_json(results))
        elif not getattr(args, "quiet", False):
            md_report = BenchmarkReportGenerator.generate_comparison_markdown(results)
            sys.stdout.write("\n" + md_report + "\n")

        return ExitCode.SUCCESS

    # 2. Pipeline Multi-Core Throughput Benchmarking (Default)
    worker_list: List[int] = [getattr(args, "workers", 4)] if getattr(args, "workers", None) else [1, 2, 4, 8]
    mock_payloads: List[bytes] = [
        f"MOCK_BENCHMARK_DOCUMENT_PAYLOAD_{i}".encode("utf-8") for i in range(iterations)
    ]

    results_data: List[Dict[str, Any]] = []
    if not getattr(args, "quiet", False) and not getattr(args, "json", False):
        sys.stdout.write("==================================================\n")
        sys.stdout.write("      scanDOC CPU Pipeline Multi-Core Benchmark   \n")
        sys.stdout.write("==================================================\n")

    for workers in worker_list:
        config = PipelineConfig(
            max_workers=workers,
            ordering_mode=OrderingMode.COMPLETION_ORDER,
        )
        pipeline = DocumentPipeline(config=config)

        t0 = time.perf_counter()
        pipeline_results = pipeline.process_many(mock_payloads)
        t1 = time.perf_counter()

        elapsed = max(0.001, t1 - t0)
        docs_per_sec = round(len(mock_payloads) / elapsed, 2)
        pages_per_sec = docs_per_sec  # Each mock doc is 1 page

        bench_info = {
            "workers": workers,
            "total_documents": len(mock_payloads),
            "elapsed_sec": round(elapsed, 4),
            "docs_per_sec": docs_per_sec,
            "pages_per_sec": pages_per_sec,
            "device": getattr(args, "device", "auto"),
        }
        results_data.append(bench_info)

        if not getattr(args, "quiet", False) and not getattr(args, "json", False):
            sys.stdout.write(
                f"Workers: {workers:2d} | Time: {elapsed:.4f}s | Docs/sec: {docs_per_sec:7.2f} | Pages/sec: {pages_per_sec:7.2f}\n"
            )

    if getattr(args, "json", False):
        print(json.dumps({"status": "completed", "benchmark_results": results_data}, indent=2))

    return ExitCode.SUCCESS
