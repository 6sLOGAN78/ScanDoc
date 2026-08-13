"""
Taxonomy enums for spatial relations and normalized semantic region categories.
"""

from enum import Enum


class SpatialRelationType(str, Enum):
    """
    Spatial directional and topological relations between document layout elements.
    """
    ABOVE = "above"
    BELOW = "below"
    LEFT_OF = "left_of"
    RIGHT_OF = "right_of"
    CONTAINS = "contains"
    CONTAINED_BY = "contained_by"
    OVERLAPS = "overlaps"
    NEAR = "near"
    CONTINUES_FROM = "continues_from"
    CONTINUES_TO = "continues_to"


class SemanticCategory(str, Enum):
    """
    Normalized visual and semantic region categories.
    """
    TEXT = "text"
    TITLE = "title"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    FIGURE = "figure"
    CAPTION = "caption"
    FORMULA = "formula"
    HEADER = "header"
    FOOTER = "footer"
    PAGE_NUMBER = "page_number"
    SIDEBAR = "sidebar"
    UNKNOWN = "unknown"
