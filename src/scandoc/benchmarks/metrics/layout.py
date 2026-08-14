"""
Layout region BoundingBox IoU, Precision, Recall, F1, and mAP metrics.
"""

from typing import Any, Dict, List, Optional, Tuple


def calculate_iou(box1: List[float], box2: List[float]) -> float:
    """
    Calculate Intersection over Union (IoU) between two bounding boxes [l, t, r, b].
    """
    if not box1 or not box2 or len(box1) < 4 or len(box2) < 4:
        return 0.0

    l1, t1, r1, b1 = box1[0], box1[1], box1[2], box1[3]
    l2, t2, r2, b2 = box2[0], box2[1], box2[2], box2[3]

    inter_l = max(l1, l2)
    inter_t = max(t1, t2)
    inter_r = min(r1, r2)
    inter_b = min(b1, b2)

    if inter_r <= inter_l or inter_b <= inter_t:
        return 0.0

    inter_area = (inter_r - inter_l) * (inter_b - inter_t)
    area1 = (r1 - l1) * (b1 - t1)
    area2 = (r2 - l2) * (b2 - t2)
    union_area = area1 + area2 - inter_area

    if union_area <= 0:
        return 0.0

    return round(float(inter_area / union_area), 4)


def calculate_layout_precision_recall(
    predictions: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]],
    iou_threshold: float = 0.5,
) -> Tuple[float, float, float]:
    """
    Calculate layout region Precision, Recall, and F1 at specified IoU threshold.
    """
    if not predictions and not ground_truth:
        return 1.0, 1.0, 1.0
    if not predictions or not ground_truth:
        return 0.0, 0.0, 0.0

    matched_gt = set()
    tp = 0

    for pred in predictions:
        p_box = pred.get("bbox")
        p_type = pred.get("type", "text")
        if not p_box:
            continue

        best_gt_idx = None
        best_iou = 0.0

        for idx, gt in enumerate(ground_truth):
            if idx in matched_gt:
                continue
            gt_box = gt.get("bbox")
            gt_type = gt.get("type", "text")
            if not gt_box or gt_type != p_type:
                continue

            iou = calculate_iou(p_box, gt_box)
            if iou > best_iou and iou >= iou_threshold:
                best_iou = iou
                best_gt_idx = idx

        if best_gt_idx is not None:
            tp += 1
            matched_gt.add(best_gt_idx)

    precision = tp / max(1, len(predictions))
    recall = tp / max(1, len(ground_truth))
    f1 = (2 * precision * recall) / max(1e-6, precision + recall)

    return round(precision, 4), round(recall, 4), round(f1, 4)


def calculate_layout_map(
    predictions: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]],
    iou_thresholds: Optional[List[float]] = None,
    iou_threshold: Optional[float] = None,
) -> float:
    """
    Calculate layout Mean Average Precision (mAP) across IoU thresholds (0.5:0.95).
    """
    if iou_threshold is not None:
        thresholds = [iou_threshold]
    else:
        thresholds = iou_thresholds or [0.5, 0.6, 0.7, 0.8, 0.9]

    maps = []
    for th in thresholds:
        prec, _, _ = calculate_layout_precision_recall(predictions, ground_truth, iou_threshold=th)
        maps.append(prec)

    return round(sum(maps) / max(1, len(maps)), 4)
