"""
Taxonomy enums for formula types, mathematical representation formats, and provider types.
"""

from enum import Enum


class FormulaType(str, Enum):
    """
    Categorization of mathematical formula expressions.
    """
    INLINE = "inline"
    DISPLAY = "display"
    NUMBERED = "numbered"
    MULTI_LINE = "multi_line"
    UNKNOWN = "unknown"


class MathFormat(str, Enum):
    """
    Mathematical syntax representation format.
    """
    LATEX = "latex"
    MATHML = "mathml"
    PLAINTEXT = "plaintext"
    UNKNOWN = "unknown"


class ProviderType(str, Enum):
    """
    Execution origin category for formula providers.
    """
    LOCAL = "local"
    HUGGINGFACE = "huggingface"
    REMOTE = "remote"
