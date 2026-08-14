"""
OCR accuracy and character recognition metrics.
"""

from typing import Dict
from scandoc.benchmarks.metrics.text import calculate_cer, calculate_wer


def evaluate_ocr_accuracy(ref_text: str, hyp_text: str) -> Dict[str, float]:
    """
    Evaluate OCR text accuracy returning CER, WER, character accuracy, and word accuracy.
    """
    cer = calculate_cer(ref_text, hyp_text)
    wer = calculate_wer(ref_text, hyp_text)
    char_acc = round(max(0.0, 1.0 - cer), 4)
    word_acc = round(max(0.0, 1.0 - wer), 4)

    return {
        "cer": cer,
        "wer": wer,
        "char_accuracy": char_acc,
        "word_accuracy": word_acc,
    }
