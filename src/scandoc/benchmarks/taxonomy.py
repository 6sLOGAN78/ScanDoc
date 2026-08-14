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


class MetricCategory(str, Enum):
    """Benchmark metric category classification."""
    TEXT = "text"
    OCR = "ocr"
    LAYOUT = "layout"
    TABLE = "table"
    FORMULA = "formula"
    STRUCTURE = "structure"
    PROFILING = "profiling"


class DocumentType(str, Enum):
    """Classification of document input fixture types."""
    DIGITAL_PDF = "digital_pdf"
    SCANNED_PDF = "scanned_pdf"
    HYBRID_PDF = "hybrid_pdf"
    IMAGE = "image"
    SYNTHETIC = "synthetic"
    UNSTRUCTURED = "unstructured"


class BenchmarkStatus(str, Enum):
    """Status state of a benchmark execution stage or test."""
    EXECUTED = "executed"
    SKIPPED = "skipped"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


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
