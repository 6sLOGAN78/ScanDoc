"""
Layout category taxonomy and versioned dataset class mapping layers (DocLayNet, PubLayNet).
"""

from enum import Enum
from typing import Dict, Union


class LayoutCategory(str, Enum):
    """
    Standard layout region category taxonomy.
    """
    TEXT = "text"
    TITLE = "title"
    HEADER = "header"
    FOOTER = "footer"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    FIGURE = "figure"
    CAPTION = "caption"
    FORMULA = "formula"
    PAGE_NUMBER = "page_number"
    UNKNOWN = "unknown"


# Standard DocLayNet 11-class dataset mapping
DOCLAYNET_MAP: Dict[Union[int, str], LayoutCategory] = {
    0: LayoutCategory.CAPTION,
    1: LayoutCategory.FOOTER,
    2: LayoutCategory.FORMULA,
    3: LayoutCategory.LIST,
    4: LayoutCategory.FOOTER,
    5: LayoutCategory.HEADER,
    6: LayoutCategory.FIGURE,
    7: LayoutCategory.TITLE,
    8: LayoutCategory.TABLE,
    9: LayoutCategory.PARAGRAPH,
    10: LayoutCategory.TITLE,
    "caption": LayoutCategory.CAPTION,
    "footnote": LayoutCategory.FOOTER,
    "formula": LayoutCategory.FORMULA,
    "list_item": LayoutCategory.LIST,
    "page_footer": LayoutCategory.FOOTER,
    "page_header": LayoutCategory.HEADER,
    "picture": LayoutCategory.FIGURE,
    "section_header": LayoutCategory.TITLE,
    "table": LayoutCategory.TABLE,
    "text": LayoutCategory.PARAGRAPH,
    "title": LayoutCategory.TITLE,
}

# Standard PubLayNet 5-class dataset mapping
PUBLAYNET_MAP: Dict[Union[int, str], LayoutCategory] = {
    0: LayoutCategory.PARAGRAPH,
    1: LayoutCategory.TITLE,
    2: LayoutCategory.LIST,
    3: LayoutCategory.TABLE,
    4: LayoutCategory.FIGURE,
    "text": LayoutCategory.PARAGRAPH,
    "title": LayoutCategory.TITLE,
    "list": LayoutCategory.LIST,
    "table": LayoutCategory.TABLE,
    "figure": LayoutCategory.FIGURE,
}


class DocLayNetMapper:
    """Mapper converting DocLayNet raw model predictions into scanDOC LayoutCategory."""

    @classmethod
    def map_class(cls, raw_id: Union[int, str]) -> LayoutCategory:
        if isinstance(raw_id, str):
            raw_id = raw_id.lower().strip()
        return DOCLAYNET_MAP.get(raw_id, LayoutCategory.UNKNOWN)


class PubLayNetMapper:
    """Mapper converting PubLayNet raw model predictions into scanDOC LayoutCategory."""

    @classmethod
    def map_class(cls, raw_id: Union[int, str]) -> LayoutCategory:
        if isinstance(raw_id, str):
            raw_id = raw_id.lower().strip()
        return PUBLAYNET_MAP.get(raw_id, LayoutCategory.UNKNOWN)
