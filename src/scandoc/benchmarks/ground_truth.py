"""
Ground truth file loading, validation, and serialization.
"""

import json
from pathlib import Path
from typing import Optional

from scandoc.benchmarks.models import GroundTruthDocument, GroundTruthElement


class GroundTruthLoader:
    """
    Utilities for loading ground truth reference metadata files (.json).
    """

    @staticmethod
    def load_ground_truth(gt_path: Path) -> Optional[GroundTruthDocument]:
        """Load ground truth metadata from JSON file."""
        if not gt_path.exists() or not gt_path.is_file():
            return None

        try:
            data = json.loads(gt_path.read_text(encoding="utf-8"))
            elements = [
                GroundTruthElement(**el) if isinstance(el, dict) else el
                for el in data.get("elements", [])
            ]
            return GroundTruthDocument(
                doc_id=data.get("doc_id", gt_path.stem),
                text_content=data.get("text_content", ""),
                elements=elements,
                tables=data.get("tables", []),
            )
        except Exception:
            return None

    @staticmethod
    def create_synthetic_ground_truth(doc_id: str, text: str) -> GroundTruthDocument:
        """Construct synthetic ground truth reference for testing."""
        return GroundTruthDocument(
            doc_id=doc_id,
            text_content=text,
            elements=[
                GroundTruthElement(
                    type="text",
                    text=text,
                    bbox=[0.1, 0.1, 0.9, 0.9],
                    page_index=0,
                )
            ],
            tables=[],
        )
