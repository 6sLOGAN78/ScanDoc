"""
Taxonomy enums for scanDOC benchmarking suite.
"""

from enum import Enum


class AdapterType(str, Enum):
    """Supported document engine adapters."""
    SCANDOC = "scandoc"
    DOCLING = "docling"
    BOTH = "both"
    ALL = "all"


class MetricType(str, Enum):
    """Supported benchmark metrics."""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    MEMORY = "memory"
    CER = "cer"
    WER = "wer"
    TEDS = "teds"
    TABLE_BLEU = "table_bleu"
    LAYOUT_MAP = "layout_map"
    IOU = "iou"


class ComparisonStatus(str, Enum):
    """Comparison result relative state."""
    BETTER = "better"
    WORSE = "worse"
    EQUAL = "approximately_equal"
    UNAVAILABLE = "unavailable"
