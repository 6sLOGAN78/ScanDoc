"""
JSON report generator for benchmark results.
"""

import json
from pathlib import Path
from typing import List, Optional, Union

from scandoc.benchmarks.models import BenchmarkResult


def generate_json_report(results: List[BenchmarkResult], output_path: Optional[Union[str, Path]] = None) -> str:
    """Generate structured JSON string or write to file."""
    data = [res.model_dump() for res in results]
    json_str = json.dumps(data, indent=2)

    if output_path:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json_str, encoding="utf-8")

    return json_str
