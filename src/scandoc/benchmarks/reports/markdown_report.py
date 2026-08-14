"""
Markdown summary table report generator for benchmark results.
"""

from pathlib import Path
from typing import List, Optional, Union

from scandoc.benchmarks.models import BenchmarkResult


def generate_markdown_report(results: List[BenchmarkResult], output_path: Optional[Union[str, Path]] = None) -> str:
    """Generate Markdown report table string or write to file."""
    lines = []
    lines.append("# scanDOC Benchmark Report")
    lines.append("")

    if results:
        env = results[0].environment
        lines.append("## Environment")
        lines.append(f"- **Git Commit**: `{env.git_commit[:8] if env.git_commit else 'unknown'}`")
        lines.append(f"- **OS**: {env.os_name}")
        lines.append(f"- **Python**: {env.python_version}")
        lines.append(f"- **CPU**: {env.cpu_model} ({env.cpu_count} cores)")
        lines.append(f"- **RAM**: {env.total_ram_gb} GB")
        lines.append(f"- **GPU**: {env.gpu_model or 'Unavailable'}")
        lines.append("")

    lines.append("## Benchmark Summary")
    lines.append("")
    lines.append("| Case ID | Adapter | Success | Pages | Warm Latency (s) | Pages/sec | Peak RAM (MB) | CER | WER |")
    lines.append("|---|---|---|---|---:|---:|---:|---:|---:|")

    for r in results:
        conv = r.conversion
        acc = r.accuracy
        perf = r.performance
        succ_str = "Yes" if conv and conv.success else "No"
        page_cnt = conv.page_count if conv else 0
        cer_str = f"{acc.cer:.4f}" if acc.cer is not None else "N/A"
        wer_str = f"{acc.wer:.4f}" if acc.wer is not None else "N/A"

        lines.append(
            f"| {r.case_id} | {r.adapter_name} | {succ_str} | {page_cnt} | {perf.warm_run_sec:.4f} | {perf.pages_per_sec} | {perf.peak_ram_mb:.2f} | {cer_str} | {wer_str} |"
        )

    lines.append("")
    md_str = "\n".join(lines)

    if output_path:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(md_str, encoding="utf-8")

    return md_str
