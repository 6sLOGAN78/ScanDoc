"""
Layout Analysis, Reading Order & Semantic Structure Subsystem for scanDOC.
"""

from scandoc.analysis.exceptions import (
    AnalysisError,
    ClassificationError,
    InvalidRegionError,
    ReadingOrderError,
)
from scandoc.analysis.layout_analyzer import LayoutAnalyzer, LayoutResult
from scandoc.analysis.semantic_classifier import SemanticClassifier
from scandoc.analysis.spatial_graph import SpatialEdge, SpatialGraph, SpatialNode
from scandoc.analysis.taxonomy import SemanticCategory, SpatialRelationType
from scandoc.analysis.tree import DocumentSection, DocumentStructureTree

__all__ = [
    "LayoutAnalyzer",
    "LayoutResult",
    "SpatialGraph",
    "SpatialNode",
    "SpatialEdge",
    "SemanticClassifier",
    "DocumentStructureTree",
    "DocumentSection",
    "SpatialRelationType",
    "SemanticCategory",
    "AnalysisError",
    "InvalidRegionError",
    "ReadingOrderError",
    "ClassificationError",
]
