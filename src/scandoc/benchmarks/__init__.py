"""
scanDOC Benchmarking & Evaluation Subsystem.
"""

from scandoc.benchmarks.adapters import ScanDocAdapter, DoclingAdapter
from scandoc.benchmarks.core import BenchmarkRunner, get_environment_meta
from scandoc.benchmarks.dataset import BenchmarkDatasetManager
from scandoc.benchmarks.ground_truth import GroundTruthLoader
from scandoc.benchmarks.models import BenchmarkCase, BenchmarkResult, GroundTruthDocument, GroundTruthElement
from scandoc.benchmarks.report import BenchmarkReportGenerator
from scandoc.benchmarks.taxonomy import AdapterType, MetricType, ComparisonStatus

__all__ = [
    "ScanDocAdapter",
    "DoclingAdapter",
    "BenchmarkRunner",
    "get_environment_meta",
    "BenchmarkDatasetManager",
    "GroundTruthLoader",
    "BenchmarkCase",
    "BenchmarkResult",
    "GroundTruthDocument",
    "GroundTruthElement",
    "BenchmarkReportGenerator",
    "AdapterType",
    "MetricType",
    "ComparisonStatus",
]
