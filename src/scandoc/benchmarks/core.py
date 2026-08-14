"""
Core benchmark runner and telemetry execution engine.
"""

import os
import platform
import subprocess
import sys
import time
import tracemalloc
from typing import Dict, List, Optional

from scandoc.benchmarks.adapters.base import BaseBenchmarkAdapter
from scandoc.benchmarks.metrics import (
    calculate_cer,
    calculate_wer,
    calculate_teds,
    calculate_table_bleu,
    calculate_iou,
    calculate_layout_map,
)
from scandoc.benchmarks.models import (
    AccuracyMetrics,
    BenchmarkCase,
    BenchmarkResult,
    BenchmarkConversionResult,
    EnvironmentMeta,
    PerformanceMetrics,
)


def get_environment_meta() -> EnvironmentMeta:
    """Collect system runtime and hardware environment metadata for reproducibility."""
    commit = "unknown"
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0:
            commit = res.stdout.strip()
    except Exception:
        pass

    gpu_model = None
    cuda_ver = None
    try:
        import torch
        if torch.cuda.is_available():
            gpu_model = torch.cuda.get_device_name(0)
            cuda_ver = torch.version.cuda
    except Exception:
        pass

    ram_gb = 0.0
    try:
        import psutil
        ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
    except Exception:
        pass

    docling_ver = None
    try:
        import docling
        docling_ver = getattr(docling, "__version__", "installed")
    except Exception:
        pass

    return EnvironmentMeta(
        git_commit=commit,
        python_version=platform.python_version(),
        os_name=f"{platform.system()} {platform.release()}",
        cpu_model=platform.processor() or platform.machine(),
        cpu_count=os.cpu_count() or 1,
        total_ram_gb=ram_gb,
        gpu_model=gpu_model,
        cuda_version=cuda_ver,
        scandoc_version="0.1.0",
        docling_version=docling_ver,
    )


class BenchmarkRunner:
    """
    Coordinates execution of benchmark cases across adapters.
    """

    def __init__(self, adapters: List[BaseBenchmarkAdapter]):
        self.adapters = adapters
        self.env_meta = get_environment_meta()

    def run_case(
        self, case: BenchmarkCase, adapter: BaseBenchmarkAdapter, iterations: int = 1, warmup: int = 0
    ) -> BenchmarkResult:
        """
        Execute benchmark case on adapter with specified warmup and iterations.
        """
        if not adapter.is_available():
            conv_fail = BenchmarkConversionResult(
                adapter_name=adapter.name,
                success=False,
                error_message=f"Adapter {adapter.name} is unavailable.",
            )
            return BenchmarkResult(
                case_id=case.case_id,
                adapter_name=adapter.name,
                environment=self.env_meta,
                performance=PerformanceMetrics(gpu_available=self.env_meta.gpu_model is not None),
                accuracy=AccuracyMetrics(),
                conversion=conv_fail,
                iterations=iterations,
                warmup=warmup,
            )

        # 1. Warmup runs
        cold_start_sec = 0.0
        for w in range(warmup):
            t_w0 = time.perf_counter()
            adapter.convert(case.file_path)
            if w == 0:
                cold_start_sec = time.perf_counter() - t_w0

        # 2. Benchmark iterations
        latencies: List[float] = []
        ram_peaks: List[float] = []
        last_conversion: Optional[BenchmarkConversionResult] = None

        for idx in range(iterations):
            conv = adapter.convert(case.file_path)
            last_conversion = conv
            if conv.success:
                latencies.append(conv.latency_sec)
                ram_peaks.append(conv.peak_ram_mb)
            if idx == 0 and cold_start_sec == 0.0:
                cold_start_sec = conv.latency_sec

        if not latencies and last_conversion:
            latencies = [last_conversion.latency_sec]
            ram_peaks = [last_conversion.peak_ram_mb]

        # Calculate Performance Telemetry
        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)
        total_lat = sum(latencies_sorted)
        mean_lat = total_lat / max(1, n)
        median_lat = latencies_sorted[n // 2]
        p95_idx = min(n - 1, int(n * 0.95))
        p99_idx = min(n - 1, int(n * 0.99))

        page_cnt = max(1, last_conversion.page_count if last_conversion else 1)
        pages_per_sec = round(page_cnt / max(0.001, mean_lat), 2)
        docs_per_sec = round(1.0 / max(0.001, mean_lat), 2)

        perf = PerformanceMetrics(
            total_latency_sec=round(total_lat, 4),
            cold_start_sec=round(cold_start_sec, 4),
            warm_run_sec=round(mean_lat, 4),
            mean_page_latency_sec=round(mean_lat / page_cnt, 4),
            median_latency_sec=round(median_lat, 4),
            p95_latency_sec=round(latencies_sorted[p95_idx], 4),
            p99_latency_sec=round(latencies_sorted[p99_idx], 4),
            docs_per_sec=docs_per_sec,
            pages_per_sec=pages_per_sec,
            peak_ram_mb=round(max(ram_peaks, default=0.0), 2),
            gpu_available=self.env_meta.gpu_model is not None,
        )

        # Calculate Accuracy Metrics if Ground Truth exists
        accuracy = AccuracyMetrics()
        if case.ground_truth and last_conversion and last_conversion.success:
            gt = case.ground_truth
            hyp_text = last_conversion.extracted_text

            if gt.text_content:
                accuracy.cer = calculate_cer(gt.text_content, hyp_text)
                accuracy.wer = calculate_wer(gt.text_content, hyp_text)

            # Table metrics if GT tables exist
            if gt.tables and last_conversion.tables:
                ref_grid = gt.tables[0].get("grid", [])
                hyp_grid = last_conversion.tables[0].get("grid", []) if last_conversion.tables else []
                if ref_grid:
                    accuracy.teds = calculate_teds(ref_grid, hyp_grid)
                    accuracy.table_bleu = calculate_table_bleu(ref_grid, hyp_grid)

            # Layout metrics if GT elements exist
            if gt.elements and last_conversion.elements:
                gt_dicts = [{"bbox": e.bbox, "type": e.type} for e in gt.elements if e.bbox]
                hyp_dicts = [{"bbox": e.get("bbox"), "type": e.get("type", "text")} for e in last_conversion.elements if e.get("bbox")]
                if gt_dicts and hyp_dicts:
                    accuracy.layout_map = calculate_layout_map(hyp_dicts, gt_dicts)
                    ious = [calculate_iou(hyp_dicts[0]["bbox"], gt_dicts[0]["bbox"])]
                    accuracy.mean_iou = round(sum(ious) / max(1, len(ious)), 4)

        return BenchmarkResult(
            case_id=case.case_id,
            adapter_name=adapter.name,
            environment=self.env_meta,
            performance=perf,
            accuracy=accuracy,
            conversion=last_conversion,
            iterations=iterations,
            warmup=warmup,
        )

    def run_all(self, cases: List[BenchmarkCase], iterations: int = 1, warmup: int = 0) -> List[BenchmarkResult]:
        """Run all cases across all registered adapters."""
        results: List[BenchmarkResult] = []
        for case in cases:
            for adapter in self.adapters:
                res = self.run_case(case, adapter, iterations=iterations, warmup=warmup)
                results.append(res)
        return results
