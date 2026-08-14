"""
Benchmark report generator for JSON serialization and Markdown comparison reports.
"""

import json
from typing import Any, Dict, List, Optional

from scandoc.benchmarks.models import BenchmarkResult
from scandoc.benchmarks.taxonomy import ComparisonStatus


class BenchmarkReportGenerator:
    """
    Generates structured JSON and Markdown comparison reports.
    """

    @staticmethod
    def to_json(results: List[BenchmarkResult]) -> str:
        """Serialize benchmark results to JSON string."""
        serialized = [r.model_dump() for r in results]
        return json.dumps({"status": "completed", "benchmark_runs": serialized}, indent=2)

    @staticmethod
    def generate_comparison_markdown(results: List[BenchmarkResult]) -> str:
        """
        Generate human-readable Markdown report comparing scanDOC vs Docling.
        """
        if not results:
            return "# scanDOC vs Docling Benchmark Report\n\nNo benchmark results available.\n"

        # Group by case_id
        grouped: Dict[str, Dict[str, BenchmarkResult]] = {}
        env_info = results[0].environment

        for r in results:
            if r.case_id not in grouped:
                grouped[r.case_id] = {}
            grouped[r.case_id][r.adapter_name] = r

        lines = [
            "# scanDOC vs Docling Empirical Benchmark Report",
            "",
            "## 1. Environment & Telemetry",
            f"- **Git Commit**: `{env_info.git_commit}`",
            f"- **OS**: {env_info.os_name}",
            f"- **Python**: {env_info.python_version}",
            f"- **CPU**: {env_info.cpu_model} ({env_info.cpu_count} cores)",
            f"- **RAM**: {env_info.total_ram_gb} GB",
            f"- **GPU**: {env_info.gpu_model or 'GPU Benchmark Unavailable (CPU-only)'}",
            f"- **Docling Version**: {env_info.docling_version or 'Unavailable'}",
            f"- **scanDOC Version**: {env_info.scandoc_version}",
            "",
            "## 2. Comparative Performance & Accuracy Table",
            "",
            "| Case ID | Adapter | Status | Latency (s) | Pages/sec | Peak RAM (MB) | CER | WER | TEDS | Comparison Status |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        for case_id, adapters in grouped.items():
            scandoc_res = adapters.get("scandoc")
            docling_res = adapters.get("docling")

            for name in ["scandoc", "docling"]:
                res = adapters.get(name)
                if not res:
                    continue

                status = "SUCCESS" if (res.conversion and res.conversion.success) else "FAILED"
                lat = f"{res.performance.warm_run_sec:.4f}"
                pps = f"{res.performance.pages_per_sec:.2f}"
                ram = f"{res.performance.peak_ram_mb:.1f}"
                cer = f"{res.accuracy.cer:.4f}" if res.accuracy.cer is not None else "N/A"
                wer = f"{res.accuracy.wer:.4f}" if res.accuracy.wer is not None else "N/A"
                teds = f"{res.accuracy.teds:.4f}" if res.accuracy.teds is not None else "N/A"

                comp_status = ComparisonStatus.UNAVAILABLE.value
                if scandoc_res and docling_res and scandoc_res.conversion.success and docling_res.conversion.success:
                    if name == "scandoc":
                        sc_lat = scandoc_res.performance.warm_run_sec
                        dc_lat = docling_res.performance.warm_run_sec
                        diff_ratio = (sc_lat - dc_lat) / max(0.0001, dc_lat)
                        if diff_ratio < -0.05:
                            comp_status = f"{ComparisonStatus.BETTER.value} ({abs(diff_ratio)*100:.1f}% faster)"
                        elif diff_ratio > 0.05:
                            comp_status = f"{ComparisonStatus.WORSE.value} ({diff_ratio*100:.1f}% slower)"
                        else:
                            comp_status = ComparisonStatus.EQUAL.value

                lines.append(
                    f"| `{case_id}` | `{name}` | {status} | {lat} | {pps} | {ram} | {cer} | {wer} | {teds} | **{comp_status}** |"
                )

        lines.extend([
            "",
            "## 3. Methodological Notes & Reproducibility",
            "- All benchmarks are derived from actual system execution; no numbers are estimated or manufactured.",
            "- Cold start latency includes initial provider/model loading time, while warm run latency reflects steady-state throughput.",
            "- Text accuracy is measured via Levenshtein distance on normalized character (CER) and word (WER) streams.",
            "",
        ])

        return "\n".join(lines)
