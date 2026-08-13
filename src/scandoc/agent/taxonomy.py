"""
Taxonomy enums for privacy policies, document capabilities, and agent lifecycle states.
"""

from enum import Enum


class PrivacyPolicy(str, Enum):
    """
    Privacy policy governing provider selection.
    """
    LOCAL_ONLY = "local_only"
    LOCAL_PREFERRED = "local_preferred"
    REMOTE_ALLOWED = "remote_allowed"
    REMOTE_ONLY = "remote_only"


class Capability(str, Enum):
    """
    Document processing capabilities required for page extraction.
    """
    NATIVE_PDF = "native_pdf"
    OCR = "ocr"
    LAYOUT = "layout"
    TABLE = "table"
    FIGURE = "figure"
    FORMULA = "formula"
    VLM = "vlm"


class AgentState(str, Enum):
    """
    Lifecycle states of the DocumentAgent control plane.
    """
    INSPECTING = "inspecting"
    PLANNING = "planning"
    EXECUTING = "executing"
    VALIDATING = "validating"
    REPLANNING = "replanning"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
