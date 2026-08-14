"""
Character Error Rate (CER), Word Error Rate (WER), and text accuracy metrics.
"""

import re
import unicodedata
from typing import Tuple


def normalize_text(text: str) -> str:
    """Normalize text with Unicode normalization, lowercase, and whitespace collapse."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def calculate_cer(ref: str, hyp: str, normalize: bool = True) -> float:
    """
    Calculate Character Error Rate (CER) using Levenshtein edit distance.
    
    CER = (Substitutions + Deletions + Insertions) / len(reference)
    """
    if normalize:
        ref = normalize_text(ref)
        hyp = normalize_text(hyp)

    if not ref:
        return 0.0 if not hyp else 1.0

    n, m = len(ref), len(hyp)
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # Deletion
                dp[i][j - 1] + 1,      # Insertion
                dp[i - 1][j - 1] + cost # Substitution
            )

    dist = dp[n][m]
    return round(float(dist / max(1, len(ref))), 4)


def calculate_wer(ref: str, hyp: str, normalize: bool = True) -> float:
    """
    Calculate Word Error Rate (WER) using word-level Levenshtein edit distance.
    """
    if normalize:
        ref = normalize_text(ref)
        hyp = normalize_text(hyp)

    ref_words = ref.split()
    hyp_words = hyp.split()

    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    n, m = len(ref_words), len(hyp_words)
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref_words[i - 1] == hyp_words[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost
            )

    dist = dp[n][m]
    return round(float(dist / max(1, len(ref_words))), 4)
