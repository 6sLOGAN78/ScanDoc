"""
Pydantic data models for reading order results and document structural hierarchy.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from scandoc.models.provenance import Provenance


class ReadingOrderItem(BaseModel):
    """
    Individual ordered block reference in reading sequence.
    """
    block_id: str = Field(..., description="ID of target document block")
    sequence_index: int = Field(..., ge=0, description="0-indexed position in reading order sequence")
    column_index: int = Field(0, ge=0, description="0-indexed column assignment")
    category: Optional[str] = Field(None, description="Block category (e.g. 'heading', 'paragraph', 'header')")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Ordering confidence score")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Ordering explanation metadata")


class ReadingOrderResult(BaseModel):
    """
    Provider-independent result of reading order reconstruction for a page.
    """
    ordered_block_ids: List[str] = Field(default_factory=list, description="Ordered sequence of block IDs")
    items: List[ReadingOrderItem] = Field(default_factory=list, description="Detailed ordered item metadata")
    algorithm_name: str = Field("RecursiveXYCut", description="Name of sorting algorithm used")
    page_index: int = Field(0, ge=0, description="Target document page index")
    processing_time_ms: float = Field(0.0, ge=0.0, description="Execution latency in ms")
    provenance: Optional[Provenance] = Field(None, description="Provenance metadata for reading order inference")


class DocumentHierarchyNode(BaseModel):
    """
    Node in structural document hierarchy tree (e.g. Section, Subsection).
    """
    node_id: str = Field(..., description="Unique ID of hierarchy node")
    title: Optional[str] = Field(None, description="Heading title text if associated")
    level: int = Field(1, ge=1, description="Heading depth level (1=H1, 2=H2, etc.)")
    block_ids: List[str] = Field(default_factory=list, description="Child block IDs belonging to this section")
    children: List["DocumentHierarchyNode"] = Field(default_factory=list, description="Child sub-sections")


class DocumentHierarchy(BaseModel):
    """
    Structured document hierarchy tree representation.
    """
    root_nodes: List[DocumentHierarchyNode] = Field(default_factory=list, description="Top-level document sections")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Hierarchy metadata")
