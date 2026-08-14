"""
Argument parser definition for scanDOC CLI subcommands.
"""

import argparse
from typing import List, Optional


from scandoc import __version__


def create_parser() -> argparse.ArgumentParser:
    """
    Build argparse ArgumentParser for scanDOC CLI commands and options.
    """
    parser = argparse.ArgumentParser(
        prog="scandoc",
        description="scanDOC: Next-Generation Document Intelligence Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"scanDOC {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 1. CONVERT Subcommand
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert documents to structured outputs (Markdown, HTML, JSON, Text, DOCX)",
    )
    convert_parser.add_argument("input", help="Path to input document file or directory")
    convert_parser.add_argument("-o", "--output", help="Target output file path for single document")
    convert_parser.add_argument("-d", "--output-dir", help="Target output directory for batch conversion")
    convert_parser.add_argument(
        "-f", "--format", default="markdown", help="Output format: markdown, html, json, text, docx (default: markdown)"
    )
    convert_parser.add_argument(
        "--device", default="auto", choices=["auto", "cpu", "cuda", "openvino", "tensorrt", "mps"], help="Hardware execution device"
    )
    convert_parser.add_argument("--provider", help="Inference provider override")
    convert_parser.add_argument("--model", help="Model ID override")
    convert_parser.add_argument("-w", "--workers", type=int, default=4, help="Pipeline worker concurrency threads (default: 4)")
    convert_parser.add_argument(
        "--on-error", default="continue-on-error", choices=["continue-on-error", "fail-fast"], help="Batch failure handling strategy"
    )
    convert_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output files")
    convert_parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose diagnostic output")
    convert_parser.add_argument("-q", "--quiet", action="store_true", help="Suppress non-essential progress output")
    convert_parser.add_argument(
        "--routing-mode", default="adaptive", choices=["adaptive", "fast", "deep", "fallback"], help="Agentic routing strategy ('adaptive', 'fast', 'deep', 'fallback')"
    )
    convert_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON summary")

    # 2. INSPECT Subcommand
    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect document characteristics, page counts, native text, and extraction paths",
    )
    inspect_parser.add_argument("input", help="Path to document file to inspect")
    inspect_parser.add_argument("-v", "--verbose", action="store_true", help="Include page-level details")
    inspect_parser.add_argument("-q", "--quiet", action="store_true", help="Suppress output")
    inspect_parser.add_argument("--json", action="store_true", help="Output inspection data in JSON format")

    # 3. SERVE Subcommand
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start scanDOC Document Intelligence HTTP API Server",
    )
    serve_parser.add_argument("--host", default="127.0.0.1", help="Binding host IP address (default: 127.0.0.1)")
    serve_parser.add_argument("-p", "--port", type=int, default=8000, help="Binding port number (default: 8000)")
    serve_parser.add_argument(
        "--device", default="auto", choices=["auto", "cpu", "cuda", "openvino", "tensorrt", "mps"], help="Hardware device target"
    )
    serve_parser.add_argument("-w", "--workers", type=int, default=4, help="Server worker threads (default: 4)")
    serve_parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose server logs")
    serve_parser.add_argument("-q", "--quiet", action="store_true", help="Suppress server banners")
    serve_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON startup status")

    # 4. BENCHMARK Subcommand
    bench_parser = subparsers.add_parser(
        "benchmark",
        help="Run CPU pipeline throughput & comparative accuracy benchmarks vs Docling",
    )
    bench_parser.add_argument("input", nargs="?", help="Optional document file or directory to benchmark")
    bench_parser.add_argument("--implementation", choices=["scandoc", "docling", "both", "all"], default="scandoc", help="Engine implementation target (scandoc, docling, both)")
    bench_parser.add_argument("--dataset", help="Path to custom benchmark dataset directory containing test files & JSON ground truths")
    bench_parser.add_argument("--compare", action="store_true", help="Generate comparative side-by-side evaluation against Docling")
    bench_parser.add_argument("-w", "--workers", type=int, help="Specific worker thread count to benchmark")
    bench_parser.add_argument("-n", "--iterations", type=int, default=5, help="Number of benchmark test iterations (default: 5)")
    bench_parser.add_argument("--warmup", type=int, default=1, help="Number of unmeasured warmup iterations (default: 1)")
    bench_parser.add_argument(
        "--device", default="auto", choices=["auto", "cpu", "cuda", "openvino", "tensorrt", "mps"], help="Hardware device target"
    )
    bench_parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose benchmark logging")
    bench_parser.add_argument("-q", "--quiet", action="store_true", help="Suppress terminal banners")
    bench_parser.add_argument("--json", action="store_true", help="Output benchmark metrics in JSON format")

    # 5. MODELS Subcommand
    models_parser = subparsers.add_parser(
        "models",
        help="Manage local model lifecycle (list, status, download, verify, clear)",
    )
    models_subparsers = models_parser.add_subparsers(dest="models_command", help="Model management action")

    # models list
    models_list = models_subparsers.add_parser("list", help="List registered and installed models")
    models_list.add_argument("--json", action="store_true", help="Output machine-readable JSON format")

    # models status
    models_status = models_subparsers.add_parser("status", help="Display model lifecycle status")
    models_status.add_argument("model_id", nargs="?", help="Optional specific model ID to inspect")
    models_status.add_argument("--json", action="store_true", help="Output machine-readable JSON format")

    # models download
    models_dl = models_subparsers.add_parser("download", help="Download model weights artifacts")
    models_dl.add_argument("model_id", nargs="?", help="Model ID to download")
    models_dl.add_argument("--all", action="store_true", help="Download all registered models")
    models_dl.add_argument("--json", action="store_true", help="Output machine-readable JSON format")

    # models verify
    models_v = models_subparsers.add_parser("verify", help="Verify SHA-256 checksums of installed model files")
    models_v.add_argument("model_id", nargs="?", help="Model ID to verify")
    models_v.add_argument("--all", action="store_true", help="Verify all installed models")
    models_v.add_argument("--json", action="store_true", help="Output machine-readable JSON format")

    # models clear
    models_c = models_subparsers.add_parser("clear", help="Clear local cached model weights")
    models_c.add_argument("model_id", nargs="?", help="Model ID to clear")
    models_c.add_argument("--all", action="store_true", help="Clear all local model caches")
    models_c.add_argument("--json", action="store_true", help="Output machine-readable JSON format")

    # 6. STUDIO Subcommand
    studio_parser = subparsers.add_parser(
        "studio",
        help="Launch embedded Visual Layout Inspector Studio Web UI server",
    )
    studio_parser.add_argument("--host", default="127.0.0.1", help="Studio server host IP (default: 127.0.0.1)")
    studio_parser.add_argument("-p", "--port", type=int, default=8000, help="Studio server port (default: 8000)")
    studio_parser.add_argument("--no-browser", dest="open_browser", action="store_false", help="Do not automatically open web browser")

    return parser
