"""
Docling benchmark runner adapter.
"""

from typing import Dict, Any
from scandoc.benchmarks.adapters.docling_adapter import DoclingAdapter


class DoclingBenchmarkRunner:
    """
    Executes Docling adapter for head-to-head comparison testing.
    """

    def __init__(self):
        self.adapter = DoclingAdapter()

    def run_benchmark(self, file_path: str) -> Dict[str, Any]:
        conv_res = self.adapter.convert(file_path)
        return {
            "conversion": conv_res,
            "is_available": self.adapter.is_available(),
        }
