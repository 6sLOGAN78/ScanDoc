"""
DocumentStructureTree maintaining hierarchical sections, headings, paragraphs, figures, and tables.
"""

from typing import Any, List, Optional
from pydantic import BaseModel, Field


class DocumentSection(BaseModel):
    """
    Hierarchical section node in document structure tree.
    """
    section_id: str = Field(..., description="Unique section ID")
    heading_text: Optional[str] = Field(None, description="Heading text string")
    level: int = Field(1, ge=1, le=6, description="Section hierarchy level (1 for H1, 2 for H2)")
    blocks: List[Any] = Field(default_factory=list, description="Ordered blocks contained in section")
    subsections: List["DocumentSection"] = Field(default_factory=list, description="Nested subsections")


class DocumentStructureTree(BaseModel):
    """
    Complete document structure tree containing root sections.
    """
    title: Optional[str] = Field(None, description="Document title")
    sections: List[DocumentSection] = Field(default_factory=list, description="Top-level document sections")
