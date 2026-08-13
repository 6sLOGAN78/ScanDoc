"""
SpatialGraph building directed spatial relationship graphs between document regions.
"""

import math
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from scandoc.analysis.taxonomy import SemanticCategory, SpatialRelationType
from scandoc.models.geometry import BoundingBox


class SpatialNode(BaseModel):
    """
    Graph node representing a document region or block with spatial geometry.
    """
    node_id: str = Field(..., description="Unique node identifier")
    bbox: BoundingBox = Field(..., description="Spatial bounding box")
    category: SemanticCategory = Field(SemanticCategory.UNKNOWN, description="Semantic category")
    reading_order_idx: int = Field(0, ge=0, description="Assigned reading order index")
    payload: Any = Field(None, description="Associated block object or payload")


class SpatialEdge(BaseModel):
    """
    Graph edge representing a spatial relationship between two nodes.
    """
    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    relation: SpatialRelationType = Field(..., description="Spatial relationship type")
    distance: float = Field(0.0, ge=0.0, description="Spatial Euclidean distance or gap")


class SpatialGraph:
    """
    Spatial graph maintaining spatial relations (ABOVE, BELOW, LEFT_OF, RIGHT_OF, NEAR, CONTAINS).
    """

    def __init__(self):
        self.nodes: Dict[str, SpatialNode] = {}
        self.edges: List[SpatialEdge] = []

    def add_node(self, node: SpatialNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, edge: SpatialEdge) -> None:
        self.edges.append(edge)

    def find_neighbors(
        self, node_id: str, relation: Optional[SpatialRelationType] = None
    ) -> List[SpatialNode]:
        """Find target nodes connected to node_id matching relation type."""
        res = []
        for e in self.edges:
            if e.source_id == node_id and (relation is None or e.relation == relation):
                if e.target_id in self.nodes:
                    res.append(self.nodes[e.target_id])
        return res

    def build_from_blocks(
        self, blocks: List[Any], page_width: float = 612.0, page_height: float = 792.0
    ) -> None:
        """
        Build spatial nodes and compute pairwise directional edges for page blocks.
        """
        for idx, b in enumerate(blocks):
            b_id = getattr(b, "id", f"b_{idx}")
            bbox = getattr(b, "bbox", BoundingBox(left=0.0, top=0.0, right=1.0, bottom=1.0, is_normalized=True))
            
            # Map block type to category
            cls_name = type(b).__name__.lower()
            cat = SemanticCategory.UNKNOWN
            if "heading" in cls_name:
                cat = SemanticCategory.HEADING
            elif "paragraph" in cls_name:
                cat = SemanticCategory.PARAGRAPH
            elif "figure" in cls_name or "image" in cls_name:
                cat = SemanticCategory.FIGURE
            elif "table" in cls_name:
                cat = SemanticCategory.TABLE
            elif "formula" in cls_name:
                cat = SemanticCategory.FORMULA

            node = SpatialNode(node_id=b_id, bbox=bbox, category=cat, reading_order_idx=idx, payload=b)
            self.add_node(node)

        # Compute pairwise spatial relationships
        node_list = list(self.nodes.values())
        for i in range(len(node_list)):
            for j in range(i + 1, len(node_list)):
                n1, n2 = node_list[i], node_list[j]
                rel, dist = self._compute_relation(n1.bbox, n2.bbox)
                if rel is not None:
                    self.add_edge(SpatialEdge(source_id=n1.node_id, target_id=n2.node_id, relation=rel, distance=dist))
                    inv_rel = self._invert_relation(rel)
                    if inv_rel:
                        self.add_edge(SpatialEdge(source_id=n2.node_id, target_id=n1.node_id, relation=inv_rel, distance=dist))

    def _compute_relation(self, b1: BoundingBox, b2: BoundingBox) -> Tuple[Optional[SpatialRelationType], float]:
        # Vertical relation check
        dy = b2.top - b1.bottom
        if dy >= -0.01:
            return SpatialRelationType.BELOW, max(0.0, dy)

        # Horizontal relation check
        dx = b2.left - b1.right
        if dx >= -0.01:
            return SpatialRelationType.RIGHT_OF, max(0.0, dx)

        return None, 0.0

    def _invert_relation(self, rel: SpatialRelationType) -> Optional[SpatialRelationType]:
        inverses = {
            SpatialRelationType.BELOW: SpatialRelationType.ABOVE,
            SpatialRelationType.ABOVE: SpatialRelationType.BELOW,
            SpatialRelationType.RIGHT_OF: SpatialRelationType.LEFT_OF,
            SpatialRelationType.LEFT_OF: SpatialRelationType.RIGHT_OF,
            SpatialRelationType.CONTAINS: SpatialRelationType.CONTAINED_BY,
            SpatialRelationType.CONTAINED_BY: SpatialRelationType.CONTAINS,
        }
        return inverses.get(rel)
