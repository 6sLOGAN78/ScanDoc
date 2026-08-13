"""
DocumentIR models package re-exporting spatial, provenance, block, and document schemas.
"""

from scandoc.models.geometry import (
    CoordOrigin,
    SizeUnit,
    Point2D,
    BoundingBox,
)
from scandoc.models.provenance import (
    ProcessingStage,
    Provenance,
)
from scandoc.models.blocks import (
    BlockType,
    TextSpan,
    BaseBlock,
    TextBlock,
    HeadingBlock,
    ParagraphBlock,
    ListItem,
    ListBlock,
    TableCell,
    TableBlock,
    ImageRef,
    FigureBlock,
    FormulaFormat,
    FormulaBlock,
    CaptionBlock,
    BlockNode,
)
from scandoc.models.document import (
    DocumentMetadata,
    Page,
    ReadingOrder,
    DocumentStructure,
    DocumentIR,
)

__all__ = [
    # Geometry
    "CoordOrigin",
    "SizeUnit",
    "Point2D",
    "BoundingBox",
    # Provenance
    "ProcessingStage",
    "Provenance",
    # Blocks
    "BlockType",
    "TextSpan",
    "BaseBlock",
    "TextBlock",
    "HeadingBlock",
    "ParagraphBlock",
    "ListItem",
    "ListBlock",
    "TableCell",
    "TableBlock",
    "ImageRef",
    "FigureBlock",
    "FormulaFormat",
    "FormulaBlock",
    "CaptionBlock",
    "BlockNode",
    # Document
    "DocumentMetadata",
    "Page",
    "ReadingOrder",
    "DocumentStructure",
    "DocumentIR",
]
