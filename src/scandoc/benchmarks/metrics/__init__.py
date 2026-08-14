"""
Benchmark metrics package.
"""

from scandoc.benchmarks.metrics.text_metrics import calculate_cer, calculate_wer, normalize_text
from scandoc.benchmarks.metrics.table_metrics import calculate_teds, calculate_table_bleu
from scandoc.benchmarks.metrics.layout_metrics import calculate_iou, calculate_layout_map

__all__ = [
    "calculate_cer",
    "calculate_wer",
    "normalize_text",
    "calculate_teds",
    "calculate_table_bleu",
    "calculate_iou",
    "calculate_layout_map",
]
