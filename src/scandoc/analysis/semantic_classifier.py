"""
SemanticClassifier evaluating font, geometry, and layout evidence for semantic block classification.
"""

import logging
import re
from typing import Any, Optional, Tuple

from scandoc.analysis.taxonomy import SemanticCategory
from scandoc.models.geometry import BoundingBox

logger = logging.getLogger("scandoc.analysis.semantic_classifier")


class SemanticClassifier:
    """
    Classifies text and structural blocks using font evidence, geometry, whitespace, and layout predictions.
    Assigns explicit confidence scores.
    """

    @classmethod
    def classify_block(
        cls,
        block: Any,
        page_height: float = 792.0,
        page_width: float = 612.0,
    ) -> Tuple[SemanticCategory, float]:
        """
        Classify block and return (SemanticCategory, confidence).
        """
        text = getattr(block, "text", "") or ""
        bbox = getattr(block, "bbox", None)

        if not text.strip():
            return SemanticCategory.UNKNOWN, 0.0

        clean_text = text.strip()

        # 1. Header / Footer / Page Number Detection by Position
        if bbox is not None and bbox.is_normalized:
            top_pos = bbox.top
            bottom_pos = bbox.bottom

            # Page Number Pattern (e.g., "Page 1", "1 of 10", "- 5 -")
            if re.match(r"^(Page\s+\d+|\d+\s+of\s+\d+|[-–—]?\s*\d+\s*[-–—]?)$", clean_text, re.IGNORECASE):
                if top_pos < 0.10 or bottom_pos > 0.90:
                    return SemanticCategory.PAGE_NUMBER, 0.95
                return SemanticCategory.PAGE_NUMBER, 0.80

            # Header / Footer Regions
            if top_pos < 0.06:
                return SemanticCategory.HEADER, 0.85
            elif bottom_pos > 0.94:
                return SemanticCategory.FOOTER, 0.85

        # 2. Heading Detection by Markdown / Font Size / Heading Block Type
        cls_name = type(block).__name__.lower()
        if "heading" in cls_name:
            return SemanticCategory.HEADING, 0.98

        if clean_text.startswith("#"):
            return SemanticCategory.HEADING, 0.92

        # 2.5 Heuristic Heading Detection (Docling/RAGFlow style fallback)
        if len(clean_text) < 120 and "\n" not in clean_text:
            # Common explicit academic/report headings
            if re.match(r"^(Abstract|References|Conclusion|Introduction|Methodology|Discussion|Results|Acknowledgments?|Appendix)$", clean_text, re.IGNORECASE):
                return SemanticCategory.HEADING, 0.90
                
            # Numbered headings (e.g., "1 Introduction", "2.1 Background", "I. Introduction", "A. Context")
            if re.match(r"^(\d+(\.\d+)*\s+[A-Z]|(?:[IVX]+|[A-Z])\.\s+[A-Z])", clean_text):
                return SemanticCategory.HEADING, 0.85
                
            # Title Case short phrases without trailing punctuation
            if clean_text.istitle() and not clean_text.endswith((".", ",", ";", ":")):
                if len(clean_text) > 3 and len(clean_text.split()) <= 8:
                    return SemanticCategory.HEADING, 0.70
            
            # ALL CAPS short phrases
            if clean_text.isupper() and len(clean_text) > 3 and len(clean_text.split()) <= 8:
                return SemanticCategory.HEADING, 0.75

        # 3. List Detection by Bullets or Numbering
        if re.match(r"^([\*\-\+]|\d+[\.\)])\s+", clean_text):
            return SemanticCategory.LIST, 0.90

        # 4. Caption Detection by Pattern (e.g. "Figure 1:", "Table 2:")
        if re.match(r"^(Figure|Fig\.|Table)\s+\d+[:\.]", clean_text, re.IGNORECASE):
            return SemanticCategory.CAPTION, 0.95

        # Default fallback to Paragraph
        return SemanticCategory.PARAGRAPH, 0.75
