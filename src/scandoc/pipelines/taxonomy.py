"""
Taxonomy enums for pipeline ordering modes and processing stage lifecycle.
"""

from enum import Enum


class OrderingMode(str, Enum):
    """
    Stream output ordering mode.
    """
    ORDERED = "ordered"
    COMPLETION_ORDER = "completion_order"


class PipelineStage(str, Enum):
    """
    Processing pipeline lifecycle stages.
    """
    INGESTION = "ingestion"
    NATIVE_EXTRACTION = "native_extraction"
    OCR = "ocr"
    LAYOUT = "layout"
    READING_ORDER = "reading_order"
    TABLE = "table"
    FORMULA = "formula"
    FIGURE = "figure"
    VLM = "vlm"
    ASSEMBLY = "assembly"
    EXPORT = "export"
