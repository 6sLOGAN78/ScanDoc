"""
Layout detection accuracy metrics: Bounding Box IoU & Layout mAP.
"""

from typing import Any, Dict, List, Tuple


def calculate_iou(box1: List[float], box2: List[float]) -> float:
    """
    Calculate Intersection over Union (IoU) for normalized boxes [l, t, r, b].
    """
    if len(box1) < 4 or len(box2) < 4:
        return 0.0

    l1, t1, r1, b1 = box1[:4]
    l2, t2, r2, b2 = box2[:4]

    inter_l = max(l1, l2)
    inter_t = max(t1, t2)
    inter_r = min(r1, r2)
    inter_b = min(b1, b2)

    inter_w = max(0.0, inter_r - inter_l)
    inter_h = max(0.0, inter_b - inter_t)
    inter_area = inter_w * inter_h

    area1 = max(0.0, r1 - l1) * max(0.0, b1 - t1)
    area2 = max(0.0, r2 - l2) * max(0.0, b2 - t2)
    union_area = area1 + area2 - inter_area

    if union_area <= 0:
        return 0.0

    return round(inter_area / union_area, 4)


def calculate_layout_map(
    predictions: List[Dict[str, Any]],
    ground_truths: List[Dict[str, Any]],
    iou_threshold: float = 0.5,
) -> float:
    """
    Calculate Layout Mean Average Precision (mAP) at specified IoU threshold.
    
    predictions: List of dicts with 'bbox', 'type', 'score'
    ground_truths: List of dicts with 'bbox', 'type'
    """
    if not ground_truths:
        return 1.0 if not predictions else 0.0
    if not predictions:
        return 0.0

    matched_gt = set()
    tp = 0
    fp = 0

    # Sort predictions by score (descending)
    preds_sorted = sorted(predictions, key=lambda x: x.get("score", 1.0), reverse=True)

    for pred in preds_sorted:
        p_box = pred.get("bbox")
        p_type = pred.get("type", "text")

        if not p_box:
            fp += 1
            continue

        best_iou = 0.0
        best_gt_idx = -1

        for gt_idx, gt in enumerate(ground_truths):
            if gt_idx in matched_gt:
                continue
            gt_box = gt.get("bbox")
            gt_type = gt.get("type", "text")

            if p_type == gt_type and gt_box:
                iou = calculate_iou(p_box, gt_box)
                if iou > best_iou:
                    best_iou = iou
                    best_gt_idx = gt_idx

        if best_iou >= iou_threshold and best_gt_idx != -1:
            tp += 1
            matched_gt.add(best_gt_idx)
        else:
            fp += 1

    fn = len(ground_truths) - len(matched_gt)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    # Simple 1-point AP approximation (Precision * Recall harmonic mean / F1 or precision at recall)
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    return round(float(f1), 4)
