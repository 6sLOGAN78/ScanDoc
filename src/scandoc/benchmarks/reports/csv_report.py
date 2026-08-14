"""
CSV spreadsheet report generator for benchmark results.
"""

import csv
import io
from pathlib import Path
from typing import List, Optional, Union

from scandoc.benchmarks.models import BenchmarkResult


def generate_csv_report(results: List[BenchmarkResult], output_path: Optional[Union[str, Path]] = None) -> str:
    """Generate CSV report string or write to file."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Case ID",
        "Adapter",
        "Success",
        "Pages",
        "Latency (s)",
        "Warm Latency (s)",
        "Pages/sec",
        "Peak RAM (MB)",
        "CER",
        "WER",
        "TEDS",
        "Mean IoU",
    ])

    for r in results:
        conv = r.conversion
        acc = r.accuracy
        perf = r.performance

        writer.writerow([
            r.case_id,
            r.adapter_name,
            conv.success if conv else False,
            conv.page_count if conv else 0,
            perf.total_latency_sec,
            perf.warm_run_sec,
            perf.pages_per_sec,
            perf.peak_ram_mb,
            acc.cer if acc.cer is not None else "",
            acc.wer if acc.wer is not None else "",
            acc.teds if acc.teds is not None else "",
            acc.mean_iou if acc.mean_iou is not None else "",
        ])

    csv_str = output.getvalue()
    if output_path:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(csv_str, encoding="utf-8")

    return csv_str
