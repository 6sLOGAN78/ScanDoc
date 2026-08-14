"""
Dynamic document classifier engine determining structural categories, page complexity, and routing strategies.
"""

from enum import Enum
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from scandoc.agent.inspector import AgentDocumentInspector, DocumentCharacteristics, PageCharacteristics
from scandoc.pdf.models import DocumentCategory

logger = logging.getLogger("scandoc.agent.classifier")


class DocumentCategoryType(str, Enum):
    """Refined classification taxonomy for document processing strategy."""
    DIGITAL_PDF = "digital_pdf"
    SCANNED_DOCUMENT = "scanned_document"
    COMPLEX_MULTI_COLUMN = "complex_multi_column"
    FORM_INVOICE = "form_invoice"
    TECHNICAL_REPORT = "technical_report"
    UNSTRUCTURED_IMAGE = "unstructured_image"


class PageComplexityScore(BaseModel):
    """Per-page difficulty and complexity score."""
    page_index: int
    complexity_score: float = Field(..., ge=0.0, le=1.0, description="Page difficulty score between 0.0 (simple) and 1.0 (complex)")
    recommended_path: str = Field("fast_path", description="Recommended path ('fast_path', 'deep_ml', 'vlm_fallback')")
    has_tables: bool = False
    has_figures: bool = False
    has_formulas: bool = False


class ClassificationResult(BaseModel):
    """Result container for document classification and routing strategy."""
    category: DocumentCategoryType
    num_pages: int
    overall_complexity: float = Field(..., ge=0.0, le=1.0)
    pages: List[PageComplexityScore] = Field(default_factory=list)
    recommended_routing: str = Field("fast_path", description="Document-level routing policy")


class DocumentClassifier:
    """
    Dynamic Document Classifier analyzing vector text density, scan likelihood, layout complexity,
    tables, figures, and math formulas to select optimal execution paths.
    """

    @classmethod
    def classify(cls, source: Union[str, Path, bytes]) -> ClassificationResult:
        """
        Inspect and classify document into a DocumentCategoryType with page complexity scores.
        """
        doc_chars: DocumentCharacteristics = AgentDocumentInspector.inspect_document(source)
        
        page_scores: List[PageComplexityScore] = []
        total_complexity = 0.0

        for p in doc_chars.pages:
            complexity = cls._calculate_page_complexity(p)
            total_complexity += complexity

            if p.native_text_ratio >= 0.85 and p.scan_probability < 0.15 and not p.has_tables and not p.has_formulas:
                path = "fast_path"
            elif p.scan_probability >= 0.80 or complexity >= 0.75:
                path = "vlm_fallback" if p.image_density >= 0.7 else "deep_ml"
            else:
                path = "deep_ml"

            page_scores.append(
                PageComplexityScore(
                    page_index=p.page_index,
                    complexity_score=round(complexity, 2),
                    recommended_path=path,
                    has_tables=p.has_tables,
                    has_figures=p.has_figures,
                    has_formulas=getattr(p, "has_formulas", False),
                )
            )

        avg_complexity = total_complexity / max(1, len(doc_chars.pages))

        # Determine overall document category
        category = cls._determine_category(doc_chars, avg_complexity)

        doc_routing = "fast_path"
        if category == DocumentCategoryType.SCANNED_DOCUMENT:
            doc_routing = "deep_ml"
        elif category in (DocumentCategoryType.COMPLEX_MULTI_COLUMN, DocumentCategoryType.TECHNICAL_REPORT):
            doc_routing = "deep_ml"
        elif avg_complexity >= 0.7:
            doc_routing = "vlm_fallback"

        return ClassificationResult(
            category=category,
            num_pages=doc_chars.num_pages,
            overall_complexity=round(avg_complexity, 2),
            pages=page_scores,
            recommended_routing=doc_routing,
        )

    @classmethod
    def _calculate_page_complexity(cls, p: PageCharacteristics) -> float:
        """Calculate weighted page complexity score (0.0 to 1.0)."""
        score = 0.0
        score += (1.0 - p.native_text_ratio) * 0.4
        score += p.scan_probability * 0.3
        score += p.image_density * 0.2
        if p.has_tables:
            score += 0.1
        if p.has_figures:
            score += 0.1
        if getattr(p, "has_formulas", False):
            score += 0.15
        return min(1.0, score)

    @classmethod
    def _determine_category(cls, doc_chars: DocumentCharacteristics, avg_complexity: float) -> DocumentCategoryType:
        if doc_chars.classification == DocumentCategory.SCANNED:
            return DocumentCategoryType.SCANNED_DOCUMENT
        
        has_any_formulas = any(getattr(p, "has_formulas", False) for p in doc_chars.pages)
        has_any_tables = any(p.has_tables for p in doc_chars.pages)
        has_any_figs = any(p.has_figures for p in doc_chars.pages)

        if has_any_formulas:
            return DocumentCategoryType.TECHNICAL_REPORT
        elif has_any_tables and avg_complexity > 0.5:
            return DocumentCategoryType.FORM_INVOICE
        elif has_any_figs and avg_complexity > 0.4:
            return DocumentCategoryType.COMPLEX_MULTI_COLUMN
        elif all(p.native_text_ratio >= 0.8 for p in doc_chars.pages):
            return DocumentCategoryType.DIGITAL_PDF
        
        return DocumentCategoryType.DIGITAL_PDF
