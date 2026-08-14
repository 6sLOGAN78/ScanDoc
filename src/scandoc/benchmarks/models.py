"""
Data models for scanDOC benchmarking subsystem.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GroundTruthElement(BaseModel):
    """Ground truth reference element."""
    type: str = "text"
    text: str = ""
    bbox: Optional[List[float]] = None  # [l, t, r, b]
    table_html: Optional[str] = None
    table_grid: Optional[List[List[str]]] = None
    page_index: int = 0


class GroundTruthDocument(BaseModel):
    """Ground truth reference document metadata."""
    doc_id: str
    text_content: str = ""
    elements: List[GroundTruthElement] = Field(default_factory=list)
    tables: List[Dict[str, Any]] = Field(default_factory=list)


class BenchmarkCase(BaseModel):
    """Individual benchmark test input case."""
    case_id: str
    file_path: str
    doc_type: str = "pdf"
    description: str = ""
    ground_truth: Optional[GroundTruthDocument] = None


class PerformanceMetrics(BaseModel):
    """Performance telemetry data."""
    total_latency_sec: float = 0.0
    cold_start_sec: float = 0.0
    warm_run_sec: float = 0.0
    mean_page_latency_sec: float = 0.0
    median_latency_sec: float = 0.0
    p95_latency_sec: float = 0.0
    p99_latency_sec: float = 0.0
    docs_per_sec: float = 0.0
    pages_per_sec: float = 0.0
    peak_ram_mb: float = 0.0
    peak_vram_mb: Optional[float] = None
    gpu_available: bool = False


class AccuracyMetrics(BaseModel):
    """Accuracy metrics against ground truth."""
    cer: Optional[float] = None  # Character Error Rate
    wer: Optional[float] = None  # Word Error Rate
    teds: Optional[float] = None  # Tree Edit Distance in Structure
    table_bleu: Optional[float] = None  # Table BLEU n-gram score
    layout_map: Optional[float] = None  # Layout Mean Average Precision
    mean_iou: Optional[float] = None  # Bounding box IoU


class EnvironmentMeta(BaseModel):
    """Reproducibility metadata."""
    git_commit: str = "unknown"
    python_version: str = ""
    os_name: str = ""
    cpu_model: str = ""
    cpu_count: int = 1
    total_ram_gb: float = 0.0
    gpu_model: Optional[str] = None
    cuda_version: Optional[str] = None
    scandoc_version: str = "0.1.0"
    docling_version: Optional[str] = None


class BenchmarkConversionResult(BaseModel):
    """Output from an individual adapter run."""
    adapter_name: str
    success: bool = True
    error_message: Optional[str] = None
    page_count: int = 0
    extracted_text: str = ""
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    elements: List[Dict[str, Any]] = Field(default_factory=list)
    latency_sec: float = 0.0
    peak_ram_mb: float = 0.0


class BenchmarkResult(BaseModel):
    """Unified benchmark result report for a case/adapter run."""
    case_id: str
    adapter_name: str
    environment: EnvironmentMeta
    performance: PerformanceMetrics
    accuracy: AccuracyMetrics
    conversion: Optional[BenchmarkConversionResult] = None
    iterations: int = 1
    warmup: int = 0
