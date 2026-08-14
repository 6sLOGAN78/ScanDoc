"""
DocumentIR structural graph metrics and node node alignment evaluation.
"""

from typing import Any, Dict, List, Tuple


def calculate_structure_node_accuracy(
    ref_blocks: List[Dict[str, Any]], hyp_blocks: List[Dict[str, Any]]
) -> Tuple[float, float, float]:
    """
    Calculate precision, recall, and F1 of DocumentIR structural block types.
    """
    if not ref_blocks and not hyp_blocks:
        return 1.0, 1.0, 1.0
    if not ref_blocks or not hyp_blocks:
        return 0.0, 0.0, 0.0

    ref_types = [b.get("type", "text") for b in ref_blocks]
    hyp_types = [b.get("type", "text") for b in hyp_blocks]

    matched = 0
    ref_types_copy = list(ref_types)
    for ht in hyp_types:
        if ht in ref_types_copy:
            matched += 1
            ref_types_copy.remove(ht)

    precision = round(matched / max(1, len(hyp_types)), 4)
    recall = round(matched / max(1, len(ref_types)), 4)
    f1 = round((2 * precision * recall) / max(1e-6, precision + recall), 4)

    return precision, recall, f1
