"""
scandoc benchmark subcommand implementation.
"""

import json
import sys
import time
from typing import Any, Dict, List

from scandoc.cli.formatter import TerminalFormatter
from scandoc.cli.taxonomy import ExitCode
from scandoc.models import DocumentIR, Page
from scandoc.pipelines import DocumentPipeline, PipelineConfig, OrderingMode


def run_benchmark(args: Any) -> int:
    """
    Execute `scandoc benchmark` subcommand.
    
    Returns:
        int: Exit code (ExitCode.SUCCESS, etc.)
    """
    worker_list: List[int] = [getattr(args, "workers", 4)] if getattr(args, "workers", None) else [1, 2, 4, 8]
    iterations: int = getattr(args, "iterations", 20)

    # Build benchmark mock payload
    mock_payloads: List[bytes] = [
        f"MOCK_BENCHMARK_DOCUMENT_PAYLOAD_{i}".encode("utf-8") for i in range(iterations)
    ]

    results: List[Dict[str, Any]] = []
    if not args.quiet and not args.json:
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
        results.append(bench_info)

        if not args.quiet and not args.json:
            sys.stdout.write(
                f"Workers: {workers:2d} | Time: {elapsed:.4f}s | Docs/sec: {docs_per_sec:7.2f} | Pages/sec: {pages_per_sec:7.2f}\n"
            )

    if args.json:
        print(json.dumps({"status": "completed", "benchmark_results": results}, indent=2))

    return ExitCode.SUCCESS
