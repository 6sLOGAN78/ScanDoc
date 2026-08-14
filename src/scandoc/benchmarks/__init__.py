"""
scanDOC Benchmarking & Evaluation Subsystem.
"""

from scandoc.benchmarks.adapters import ScanDocAdapter, DoclingAdapter
from scandoc.benchmarks.config import BenchmarkConfig
from scandoc.benchmarks.core import BenchmarkRunner, get_environment_meta
from scandoc.benchmarks.dataset import BenchmarkDatasetManager
from scandoc.benchmarks.datasets import DatasetManager
from scandoc.benchmarks.ground_truth import GroundTruthLoader
from scandoc.benchmarks.manifest import DocumentCorpusManifest, ManifestDocument
from scandoc.benchmarks.models import BenchmarkCase, BenchmarkResult, GroundTruthDocument, GroundTruthElement
from scandoc.benchmarks.report import BenchmarkReportGenerator
from scandoc.benchmarks.reports import generate_csv_report, generate_json_report, generate_markdown_report
from scandoc.benchmarks.runner import run_benchmark_suite
from scandoc.benchmarks.taxonomy import AdapterType, BenchmarkStatus, ComparisonStatus, DocumentType, MetricCategory, MetricType

__all__ = [
    "ScanDocAdapter",
    "DoclingAdapter",
    "BenchmarkConfig",
    "BenchmarkRunner",
    "get_environment_meta",
    "DatasetManager",
    "BenchmarkDatasetManager",
    "GroundTruthLoader",
    "DocumentCorpusManifest",
    "ManifestDocument",
    "BenchmarkCase",
    "BenchmarkResult",
    "GroundTruthDocument",
    "GroundTruthElement",
    "BenchmarkReportGenerator",
    "generate_json_report",
    "generate_csv_report",
    "generate_markdown_report",
    "run_benchmark_suite",
    "AdapterType",
    "MetricCategory",
    "DocumentType",
    "BenchmarkStatus",
    "MetricType",
    "ComparisonStatus",
]
