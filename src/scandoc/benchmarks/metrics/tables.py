"""
Table structure recognition metrics (TEDS, Table BLEU, row/column count accuracy).
"""

from typing import Any, Dict, List
from scandoc.benchmarks.metrics.text import calculate_cer, calculate_wer


def calculate_teds(ref_grid: List[List[str]], hyp_grid: List[List[str]]) -> float:
    """
    Calculate simplified Tree Edit Distance in Structure (TEDS) score for table grid matrix.
    """
    if not ref_grid and not hyp_grid:
        return 1.0
    if not ref_grid or not hyp_grid:
        return 0.0

    ref_rows, ref_cols = len(ref_grid), max(len(r) for r in ref_grid) if ref_grid else 0
    hyp_rows, hyp_cols = len(hyp_grid), max(len(r) for r in hyp_grid) if hyp_grid else 0

    grid_match = 1.0 - (abs(ref_rows - hyp_rows) + abs(ref_cols - hyp_cols)) / max(1, ref_rows + ref_cols + hyp_rows + hyp_cols)
    grid_match = max(0.0, grid_match)

    cell_accs = []
    min_r = min(ref_rows, hyp_rows)
    min_c = min(ref_cols, hyp_cols)

    for r in range(min_r):
        for c in range(min_c):
            ref_cell = ref_grid[r][c] if len(ref_grid[r]) > c else ""
            hyp_cell = hyp_grid[r][c] if len(hyp_grid[r]) > c else ""
            cer = calculate_cer(ref_cell, hyp_cell)
            cell_accs.append(1.0 - cer)

    mean_cell_acc = sum(cell_accs) / max(1, len(cell_accs)) if cell_accs else 0.0
    teds = round(0.5 * grid_match + 0.5 * mean_cell_acc, 4)
    return max(0.0, min(1.0, teds))


def calculate_table_bleu(ref_grid: List[List[str]], hyp_grid: List[List[str]]) -> float:
    """
    Calculate Table BLEU n-gram cell text match score.
    """
    ref_flat = [c.strip() for r in ref_grid for c in r if c.strip()]
    hyp_flat = [c.strip() for r in hyp_grid for c in r if c.strip()]

    if not ref_flat and not hyp_flat:
        return 1.0
    if not ref_flat or not hyp_flat:
        return 0.0

    matches = sum(1 for c in hyp_flat if c in ref_flat)
    bleu = round(float(matches / max(len(ref_flat), len(hyp_flat))), 4)
    return bleu
