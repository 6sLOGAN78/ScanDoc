"""
Formula comparison and LaTeX mathematical string metrics.
"""

import re
from scandoc.benchmarks.metrics.text import calculate_cer, calculate_wer


def normalize_latex(latex_str: str) -> str:
    """Normalize LaTeX formula string for string comparison."""
    if not latex_str:
        return ""
    s = latex_str.strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\\\s+", r"\\", s)
    return s.strip()


def calculate_formula_exact_match(ref_latex: str, hyp_latex: str) -> float:
    """Return 1.0 if normalized LaTeX strings match exactly, else 0.0."""
    n_ref = normalize_latex(ref_latex)
    n_hyp = normalize_latex(hyp_latex)
    return 1.0 if n_ref == n_hyp else 0.0


def calculate_formula_similarity(ref_latex: str, hyp_latex: str) -> float:
    """Calculate token similarity between two LaTeX formula strings."""
    n_ref = normalize_latex(ref_latex)
    n_hyp = normalize_latex(hyp_latex)
    cer = calculate_cer(n_ref, n_hyp, normalize=False)
    return round(max(0.0, 1.0 - cer), 4)
