"""
Table structure & content accuracy metrics: TEDS & Table BLEU.
"""

from collections import Counter
import math
import re
from typing import Any, List, Union


def _extract_grid_tokens(grid: List[List[Any]]) -> List[str]:
    """Flatten 2D grid matrix into token list."""
    tokens: List[str] = []
    for row in grid:
        for cell in row:
            text = str(cell).strip()
            if text:
                tokens.extend(text.lower().split())
    return tokens


def calculate_table_bleu(
    ref_grid: List[List[Any]], hyp_grid: List[List[Any]], max_n: int = 4
) -> float:
    """
    Calculate Table BLEU score based on cell n-gram overlap.
    """
    ref_tokens = _extract_grid_tokens(ref_grid)
    hyp_tokens = _extract_grid_tokens(hyp_grid)

    if not ref_tokens:
        return 1.0 if not hyp_tokens else 0.0
    if not hyp_tokens:
        return 0.0

    # Brevity penalty
    c = len(hyp_tokens)
    r = len(ref_tokens)
    bp = math.exp(1 - r / c) if c < r else 1.0

    p_ns = []
    for n in range(1, max_n + 1):
        ref_ngrams = Counter([tuple(ref_tokens[i:i + n]) for i in range(len(ref_tokens) - n + 1)])
        hyp_ngrams = Counter([tuple(hyp_tokens[i:i + n]) for i in range(len(hyp_tokens) - n + 1)])

        if not hyp_ngrams:
            p_ns.append(1e-9)
            continue

        overlap = sum((hyp_ngrams & ref_ngrams).values())
        total = sum(hyp_ngrams.values())
        p_n = overlap / total if total > 0 else 1e-9
        p_ns.append(max(1e-9, p_n))

    s = sum(math.log(p) for p in p_ns) / max_n
    bleu = bp * math.exp(s)
    return round(float(bleu), 4)


def calculate_teds(
    ref_grid_or_html: Union[List[List[Any]], str],
    hyp_grid_or_html: Union[List[List[Any]], str],
) -> float:
    """
    Calculate TEDS (Tree Edit Distance in Structure) approximation for table structures.
    Compairs structural row/col count and cell match similarity.
    """
    if isinstance(ref_grid_or_html, list) and isinstance(hyp_grid_or_html, list):
        r_rows, r_cols = len(ref_grid_or_html), max((len(r) for r in ref_grid_or_html), default=0)
        h_rows, h_cols = len(hyp_grid_or_html), max((len(r) for r in hyp_grid_or_html), default=0)

        if r_rows == 0 and h_rows == 0:
            return 1.0
        if r_rows == 0 or h_rows == 0:
            return 0.0

        row_sim = 1.0 - abs(r_rows - h_rows) / max(r_rows, h_rows)
        col_sim = 1.0 - abs(r_cols - h_cols) / max(r_cols, h_cols)

        # Content match score
        ref_toks = _extract_grid_tokens(ref_grid_or_html)
        hyp_toks = _extract_grid_tokens(hyp_grid_or_html)
        common = sum((Counter(hyp_toks) & Counter(ref_toks)).values())
        total = max(1, len(ref_toks))
        content_sim = common / total

        teds = 0.4 * row_sim + 0.4 * col_sim + 0.2 * content_sim
        return round(max(0.0, min(1.0, float(teds))), 4)

    # Simple fallback string similarity for HTML
    ref_s = str(ref_grid_or_html)
    hyp_s = str(hyp_grid_or_html)
    if ref_s == hyp_s:
        return 1.0
    return 0.5
