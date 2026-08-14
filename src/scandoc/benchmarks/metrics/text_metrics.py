"""
Text accuracy metrics: Character Error Rate (CER) & Word Error Rate (WER).
"""

import re
from typing import Any, List


def normalize_text(text: str) -> str:
    """
    Standardize text formatting before comparison.
    Normalizes whitespace and converts to lowercase.
    """
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()


def levenshtein_distance(seq1: List[Any], seq2: List[Any]) -> int:
    """Calculate exact Levenshtein edit distance between two sequences."""
    n1, n2 = len(seq1), len(seq2)
    if n1 == 0:
        return n2
    if n2 == 0:
        return n1

    dp = list(range(n2 + 1))
    for i in range(1, n1 + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n2 + 1):
            temp = dp[j]
            cost = 0 if seq1[i - 1] == seq2[j - 1] else 1
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + cost)
            prev = temp
    return dp[n2]


def calculate_cer(reference: str, hypothesis: str, normalize: bool = True) -> float:
    """
    Calculate Character Error Rate (CER).
    CER = LevenshteinDistance(ref, hyp) / len(ref)
    """
    if normalize:
        ref = normalize_text(reference)
        hyp = normalize_text(hypothesis)
    else:
        ref = reference
        hyp = hypothesis

    if not ref:
        return 0.0 if not hyp else 1.0

    ref_chars = list(ref)
    hyp_chars = list(hyp)
    dist = levenshtein_distance(ref_chars, hyp_chars)
    return round(dist / len(ref_chars), 4)


def calculate_wer(reference: str, hypothesis: str, normalize: bool = True) -> float:
    """
    Calculate Word Error Rate (WER).
    WER = LevenshteinDistance(ref_words, hyp_words) / len(ref_words)
    """
    if normalize:
        ref = normalize_text(reference)
        hyp = normalize_text(hypothesis)
    else:
        ref = reference
        hyp = hypothesis

    ref_words = ref.split()
    hyp_words = hyp.split()

    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    dist = levenshtein_distance(ref_words, hyp_words)
    return round(dist / len(ref_words), 4)
