"""
Reproducible CPU multi-core benchmark script measuring pages/second throughput across worker counts.
"""

import time
from scandoc.pipelines import DocumentPipeline, PipelineConfig, OrderingMode


def run_cpu_benchmark():
    """Benchmark document throughput across worker thread counts (1, 2, 4, 8)."""
    sample_doc = b"# Benchmark Document Title\n\n" + (b"This is benchmark paragraph content. " * 50) + b"\n\n"
    num_docs = 20
    docs = [sample_doc for _ in range(num_docs)]

    print("==================================================")
    print("      scanDOC CPU Pipeline Multi-Core Benchmark   ")
    print("==================================================")

    for workers in [1, 2, 4, 8]:
        config = PipelineConfig(max_workers=workers, ordering_mode=OrderingMode.COMPLETION_ORDER)
        pipeline = DocumentPipeline(config=config)

        start = time.perf_counter()
        results = list(pipeline.stream(docs))
        elapsed = time.perf_counter() - start

        total_pages = sum(r.metrics.pages_processed for r in results if r.status == "success")
        pages_per_sec = total_pages / elapsed if elapsed > 0 else 0.0
        docs_per_sec = num_docs / elapsed if elapsed > 0 else 0.0

        print(f"Workers: {workers} | Time: {elapsed:.3f}s | Docs/sec: {docs_per_sec:.2f} | Pages/sec: {pages_per_sec:.2f}")


if __name__ == "__main__":
    run_cpu_benchmark()
