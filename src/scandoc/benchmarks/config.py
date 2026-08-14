"""
Configuration settings for scanDOC benchmark execution framework.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class BenchmarkConfig(BaseModel):
    """
    Configuration options for scanDOC benchmark runner.
    """
    dataset_manifest_path: Optional[str] = Field(None, description="Path to dataset manifest JSON")
    output_dir: str = Field("benchmarks/results", description="Directory to store benchmark reports")
    warmup: int = Field(1, ge=0, description="Warmup iterations before timing")
    iterations: int = Field(3, ge=1, description="Measured benchmark iterations")
    docling_enabled: bool = Field(True, description="Run Docling comparison if docling is installed")
    device: str = Field("auto", description="Execution device ('cpu', 'cuda', 'auto')")
    SCANDOC_OFFLINE: bool = Field(default_factory=lambda: os.getenv("SCANDOC_OFFLINE", "0").lower() in ("1", "true", "yes"))
    profile_stages: bool = Field(True, description="Enable per-stage latency profiling")
    regression_thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "max_cer": 0.15,
            "max_wer": 0.25,
            "min_layout_f1": 0.70,
            "max_latency_regression_pct": 20.0,
        },
        description="Thresholds for detecting regression",
    )
