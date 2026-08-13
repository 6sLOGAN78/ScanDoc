"""
Taxonomy enums for figure categories and provider types.
"""

from enum import Enum


class FigureType(str, Enum):
    """
    Standard figure and image category taxonomy.
    """
    FIGURE = "figure"
    PHOTOGRAPH = "photograph"
    DIAGRAM = "diagram"
    CHART = "chart"
    GRAPH = "graph"
    ILLUSTRATION = "illustration"
    LOGO = "logo"
    DECORATIVE = "decorative"
    SCANNED_IMAGE = "scanned_image"
    UNKNOWN = "unknown"


class ProviderType(str, Enum):
    """
    Execution origin category for figure providers.
    """
    LOCAL = "local"
    HUGGINGFACE = "huggingface"
    REMOTE = "remote"
