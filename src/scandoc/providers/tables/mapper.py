"""
Deterministic spatial mapping engine associating OCR and native text regions into table cells.
"""

import logging
from typing import Any, Dict, List, Union

from scandoc.models.blocks import TextBlock
from scandoc.providers.ocr.models import OCRTextRegion
from scandoc.providers.tables.models import TableCellStructure

logger = logging.getLogger("scandoc.providers.tables.mapper")


class OcrToCellMapper:
    """
    Maps OCR text regions or native text blocks into table grid cells based on spatial bounding box intersection.
    """

    @classmethod
    def map_text_to_cells(
        self,
        cells: List[TableCellStructure],
        text_sources: List[Union[OCRTextRegion, TextBlock, Any]],
        overlap_threshold: float = 0.3,
    ) -> List[TableCellStructure]:
        """
        Assign text contents to table cells using geometric bounding box intersection over cell area.
        
        Args:
            cells: List of TableCellStructure models representing table grid.
            text_sources: List of OCRTextRegion or TextBlock objects containing text and bounding boxes.
            overlap_threshold: Minimum intersection over text area fraction required.
            
        Returns:
            Updated list of TableCellStructure objects with text fields populated.
        """
        if not cells or not text_sources:
            return cells

        # Storage mapping cell_id -> List[(top, left, text)]
        cell_text_map: Dict[str, List[tuple[float, float, str]]] = {c.cell_id: [] for c in cells}

        for ts in text_sources:
            txt = getattr(ts, "text", "").strip()
            bbox = getattr(ts, "bbox", None)
            if not txt or bbox is None:
                continue

            t_left, t_top, t_right, t_bottom = bbox.left, bbox.top, bbox.right, bbox.bottom
            t_area = max(1e-6, (t_right - t_left) * (t_bottom - t_top))

            best_cell_id = None
            best_overlap_ratio = 0.0

            for cell in cells:
                c_left, c_top, c_right, c_bottom = cell.bbox.left, cell.bbox.top, cell.bbox.right, cell.bbox.bottom

                # Compute intersection rectangle
                i_left = max(t_left, c_left)
                i_top = max(t_top, c_top)
                i_right = min(t_right, c_right)
                i_bottom = min(t_bottom, c_bottom)

                if i_right > i_left and i_bottom > i_top:
                    i_area = (i_right - i_left) * (i_bottom - i_top)
                    ratio = i_area / t_area
                    if ratio > best_overlap_ratio and ratio >= overlap_threshold:
                        best_overlap_ratio = ratio
                        best_cell_id = cell.cell_id

            if best_cell_id is not None:
                cell_text_map[best_cell_id].append((t_top, t_left, txt))

        # Update cell texts in sequence order
        updated_cells: List[TableCellStructure] = []
        for cell in cells:
            assigned = cell_text_map.get(cell.cell_id, [])
            if assigned:
                # Sort top to bottom, left to right
                assigned_sorted = sorted(assigned, key=lambda x: (x[0], x[1]))
                concat_text = " ".join(item[2] for item in assigned_sorted)
                cell_copy = cell.model_copy(update={"text": concat_text})
                updated_cells.append(cell_copy)
            else:
                updated_cells.append(cell)

        return updated_cells
