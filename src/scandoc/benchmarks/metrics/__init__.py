"""
Benchmark evaluation metrics subsystem.
"""

from scandoc.benchmarks.metrics.formulas import (
    calculate_formula_exact_match,
    calculate_formula_similarity,
)
from scandoc.benchmarks.metrics.layout import (
    calculate_iou,
    calculate_layout_map,
    calculate_layout_precision_recall,
)
from scandoc.benchmarks.metrics.ocr import evaluate_ocr_accuracy
from scandoc.benchmarks.metrics.structure import calculate_structure_node_accuracy
from scandoc.benchmarks.metrics.tables import calculate_table_bleu, calculate_teds
from scandoc.benchmarks.metrics.text import calculate_cer, calculate_wer, normalize_text

__all__ = [
    "calculate_cer",
    "calculate_wer",
    "normalize_text",
    "evaluate_ocr_accuracy",
    "calculate_iou",
    "calculate_layout_precision_recall",
    "calculate_layout_map",
    "calculate_teds",
    "calculate_table_bleu",
    "calculate_formula_exact_match",
    "calculate_formula_similarity",
    "calculate_structure_node_accuracy",
]
