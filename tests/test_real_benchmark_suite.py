"""
Comprehensive test suite for Phase 33: End-to-End Benchmarking & Docling Parity Verification.
"""

import json
from pathlib import Path
import pytest

from scandoc.benchmarks import (
    BenchmarkCase,
    BenchmarkConfig,
    BenchmarkRunner,
    DatasetManager,
    DoclingAdapter,
    DocumentCorpusManifest,
    ManifestDocument,
    ScanDocAdapter,
    generate_csv_report,
    generate_json_report,
    generate_markdown_report,
    get_environment_meta,
    run_benchmark_suite,
)
from scandoc.benchmarks.metrics import (
    calculate_cer,
    calculate_formula_exact_match,
    calculate_formula_similarity,
    calculate_iou,
    calculate_layout_map,
    calculate_structure_node_accuracy,
    calculate_table_bleu,
    calculate_teds,
    calculate_wer,
)
from scandoc.benchmarks.profiling import StageTimer, MemoryProfiler, get_cpu_telemetry, get_gpu_telemetry
from fixtures.pdf_fixtures import generate_digital_pdf_bytes


@pytest.fixture
def pdf_test_file(tmp_path) -> Path:
    p = tmp_path / "bench_test_doc.pdf"
    p.write_bytes(generate_digital_pdf_bytes(text="Phase 33 End to End Benchmark Content"))
    return p


# 1. Corpus Manifest & Dataset Manager Tests
def test_manifest_parsing(tmp_path):
    manifest_data = {
        "dataset_name": "Test Corpus",
        "version": "1.0.0",
        "description": "Test dataset description",
        "documents": [
            {
                "id": "doc_001",
                "path": str(tmp_path / "doc.pdf"),
                "doc_type": "digital_pdf",
                "page_count": 2,
            }
        ],
    }
    m_path = tmp_path / "manifest.json"
    m_path.write_text(json.dumps(manifest_data), encoding="utf-8")

    mgr = DatasetManager(manifest_path=str(m_path))
    assert mgr.manifest is not None
    assert mgr.manifest.dataset_name == "Test Corpus"
    assert mgr.manifest.find_document("doc_001") is not None


def test_dataset_fixture_discovery():
    mgr = DatasetManager()
    cases = mgr.get_benchmark_cases()
    assert isinstance(cases, list)


# 2. Formula & Structure Metrics Tests
def test_formula_metrics():
    latex_ref = r"\frac{a}{b} + c^2"
    latex_hyp = r"\frac{a}{b} + c^2"
    latex_diff = r"a/b + c"

    assert calculate_formula_exact_match(latex_ref, latex_hyp) == 1.0
    assert calculate_formula_similarity(latex_ref, latex_hyp) == 1.0
    assert calculate_formula_exact_match(latex_ref, latex_diff) == 0.0


def test_structure_metrics():
    ref_blocks = [{"type": "title"}, {"type": "paragraph"}, {"type": "table"}]
    hyp_blocks = [{"type": "title"}, {"type": "paragraph"}, {"type": "table"}]
    hyp_diff = [{"type": "title"}]

    p, r, f1 = calculate_structure_node_accuracy(ref_blocks, hyp_blocks)
    assert (p, r, f1) == (1.0, 1.0, 1.0)

    p_d, r_d, f1_d = calculate_structure_node_accuracy(ref_blocks, hyp_diff)
    assert p_d == 1.0
    assert r_d < 1.0


# 3. Latency & Memory Profiler Tests
def test_stage_timer_profiling():
    timer = StageTimer()
    with timer.measure("ocr_stage"):
        pass

    assert "ocr_stage" in timer.stage_timings
    assert timer.stage_timings["ocr_stage"] >= 0.0


def test_memory_and_telemetry_profiling():
    mem_prof = MemoryProfiler()
    rss = mem_prof.get_current_rss_mb()
    assert rss >= 0.0

    cpu_tele = get_cpu_telemetry()
    assert cpu_tele["cpu_count"] >= 1

    gpu_tele = get_gpu_telemetry()
    # If CUDA unavailable, gpu_tele must be None
    if gpu_tele is not None:
        assert "vram_allocated_mb" in gpu_tele


# 4. JSON, CSV, and Markdown Report Generators
def test_report_generators(pdf_test_file):
    sc_adapter = ScanDocAdapter()
    case = BenchmarkCase(case_id="bench_report_case", file_path=str(pdf_test_file))
    runner = BenchmarkRunner(adapters=[sc_adapter])
    results = runner.run_all([case], iterations=1, warmup=0)

    json_str = generate_json_report(results)
    assert "bench_report_case" in json_str

    csv_str = generate_csv_report(results)
    assert "bench_report_case" in csv_str
    assert "Case ID" in csv_str

    md_str = generate_markdown_report(results)
    assert "# scanDOC Benchmark Report" in md_str
    assert "bench_report_case" in md_str


# 5. Full Benchmark Suite Orchestration Test
def test_full_benchmark_suite_runner(pdf_test_file):
    cfg = BenchmarkConfig(warmup=0, iterations=1, docling_enabled=False)
    case = BenchmarkCase(case_id="suite_test", file_path=str(pdf_test_file))
    results = run_benchmark_suite(config=cfg, cases=[case])

    assert len(results) >= 1
    assert results[0].case_id == "suite_test"
    assert results[0].conversion.success is True
