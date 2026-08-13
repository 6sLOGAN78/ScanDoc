"""
Taxonomy enums for VLM task types, execution modes, and provider types.
"""

from enum import Enum


class VlmTaskType(str, Enum):
    """
    Task categories for Vision-Language Models.
    """
    PAGE_UNDERSTANDING = "page_understanding"
    FIGURE_UNDERSTANDING = "figure_understanding"
    TABLE_UNDERSTANDING = "table_understanding"
    FORMULA_UNDERSTANDING = "formula_understanding"
    DOCUMENT_VALIDATION = "document_validation"
    OCR_CORRECTION = "ocr_correction"
    LAYOUT_VALIDATION = "layout_validation"
    CAPTION_GENERATION = "caption_generation"
    STRUCTURE_EXTRACTION = "structure_extraction"
    CUSTOM = "custom"


class VlmExecutionMode(str, Enum):
    """
    Execution location mode for VLM metadata tracking.
    """
    LOCAL = "local"
    REMOTE = "remote"


class ProviderType(str, Enum):
    """
    Origin category for VLM providers.
    """
    LOCAL = "local"
    HUGGINGFACE = "huggingface"
    REMOTE = "remote"
