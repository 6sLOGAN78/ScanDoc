"""
Comprehensive test suite for Phase 24: Benchmarking Suite & Production Release Packaging.
"""

import json
from pathlib import Path
import subprocess
import sys
import pytest

from scandoc.benchmarks import (
    AdapterType,
    BenchmarkCase,
    BenchmarkDatasetManager,
    BenchmarkReportGenerator,
    BenchmarkRunner,
    DoclingAdapter,
    GroundTruthDocument,
    GroundTruthElement,
    GroundTruthLoader,
    ScanDocAdapter,
    get_environment_meta,
)
from scandoc.benchmarks.metrics import (
    calculate_cer,
    calculate_iou,
    calculate_layout_map,
    calculate_table_bleu,
    calculate_teds,
    calculate_wer,
    normalize_text,
)
from scandoc.cli import main
from scandoc.cli.taxonomy import ExitCode
from fixtures.pdf_fixtures import generate_digital_pdf_bytes


@pytest.fixture
def test_pdf_path(tmp_path) -> Path:
    p = tmp_path / "test_bench_doc.pdf"
    p.write_bytes(generate_digital_pdf_bytes(text="scanDOC Test Benchmark Document"))
    return p


# 1. Text Metrics Tests (CER / WER / Normalization)
def test_text_metrics_cer_wer():
    ref = "The quick brown fox jumps over the lazy dog"
    hyp_exact = "The quick brown fox jumps over the lazy dog"
    hyp_error = "The quick brown fox jumps over lazy dog"

    assert calculate_cer(ref, hyp_exact) == 0.0
    assert calculate_wer(ref, hyp_exact) == 0.0

    cer_err = calculate_cer(ref, hyp_error)
    wer_err = calculate_wer(ref, hyp_error)

    assert 0.0 < cer_err < 0.2
    assert 0.0 < wer_err < 0.3
    assert normalize_text("  Hello  WORLD!  ") == "hello world!"


# 2. Table Metrics Tests (TEDS / Table BLEU)
def test_table_metrics_teds_bleu():
    grid_ref = [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]]
    grid_hyp = [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]]
    grid_diff = [["Name", "Age"], ["Alice", "31"]]

    assert calculate_teds(grid_ref, grid_hyp) == 1.0
    assert calculate_table_bleu(grid_ref, grid_hyp) == 1.0

    teds_diff = calculate_teds(grid_ref, grid_diff)
    bleu_diff = calculate_table_bleu(grid_ref, grid_diff)

    assert 0.0 <= teds_diff < 1.0
    assert 0.0 <= bleu_diff < 1.0


# 3. Layout Metrics Tests (IoU / Layout mAP)
def test_layout_metrics_iou_map():
    box1 = [0.1, 0.1, 0.5, 0.5]
    box2 = [0.1, 0.1, 0.5, 0.5]
    box3 = [0.6, 0.6, 0.9, 0.9]

    assert calculate_iou(box1, box2) == 1.0
    assert calculate_iou(box1, box3) == 0.0

    preds = [{"bbox": box1, "type": "title", "score": 0.95}]
    gts = [{"bbox": box2, "type": "title"}]

    assert calculate_layout_map(preds, gts, iou_threshold=0.5) == 1.0


# 4. Environment Metadata Test
def test_environment_metadata():
    env = get_environment_meta()
    assert env.scandoc_version == "0.1.0"
    assert env.python_version != ""
    assert env.os_name != ""
    assert env.cpu_count >= 1


# 5. Ground Truth Loader & Dataset Manager Tests
def test_ground_truth_and_dataset(test_pdf_path):
    gt = GroundTruthLoader.create_synthetic_ground_truth("test_doc", "Ground Truth Text")
    assert gt.doc_id == "test_doc"
    assert len(gt.elements) == 1

    ds_mgr = BenchmarkDatasetManager()
    cases = ds_mgr.get_cases()
    assert len(cases) >= 1
    ds_mgr.cleanup()


# 6. Adapter Tests (scanDOC & Docling)
def test_scandoc_adapter(test_pdf_path):
    adapter = ScanDocAdapter()
    assert adapter.name == "scandoc"
    assert adapter.is_available() is True

    res = adapter.convert(str(test_pdf_path))
    assert res.success is True
    assert res.latency_sec >= 0.0
    assert "scanDOC Test Benchmark Document" in res.extracted_text


def test_docling_adapter(test_pdf_path):
    adapter = DoclingAdapter()
    assert adapter.name == "docling"
    
    res = adapter.convert(str(test_pdf_path))
    if not adapter.is_available() or not res.success:
        assert res.success is False
        assert res.error_message is not None
    else:
        assert res.success is True


# 7. Benchmark Runner & Telemetry Test
def test_benchmark_runner(test_pdf_path):
    sc_adapter = ScanDocAdapter()
    conv = sc_adapter.convert(str(test_pdf_path))
    gt = GroundTruthLoader.create_synthetic_ground_truth("test_case", conv.extracted_text)
    case = BenchmarkCase(case_id="test_case", file_path=str(test_pdf_path), doc_type="pdf", ground_truth=gt)

    runner = BenchmarkRunner(adapters=[sc_adapter])
    bench_res = runner.run_case(case, sc_adapter, iterations=2, warmup=1)

    assert bench_res.case_id == "test_case"
    assert bench_res.performance.total_latency_sec > 0.0
    assert bench_res.performance.warm_run_sec > 0.0
    assert bench_res.performance.pages_per_sec > 0.0
    assert bench_res.accuracy.cer is not None
    assert bench_res.accuracy.cer == 0.0


# 8. Report Generator Test (JSON & Markdown)
def test_benchmark_report_generator(test_pdf_path):
    sc_adapter = ScanDocAdapter()
    case = BenchmarkCase(case_id="report_case", file_path=str(test_pdf_path))
    runner = BenchmarkRunner(adapters=[sc_adapter])
    results = runner.run_all([case], iterations=1, warmup=0)

    json_out = BenchmarkReportGenerator.to_json(results)
    data = json.loads(json_out)
    assert data["status"] == "completed"
    assert len(data["benchmark_runs"]) == 1

    md_out = BenchmarkReportGenerator.generate_comparison_markdown(results)
    assert "scanDOC vs Docling Empirical Benchmark Report" in md_out
    assert "`report_case`" in md_out


# 9. CLI Benchmark Comparative Integration Test
def test_cli_benchmark_comparative(test_pdf_path, capsys):
    ret = main(["benchmark", "--implementation", "scandoc", "-n", "1", "--json"])
    assert ret == ExitCode.SUCCESS
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "benchmark_runs" in data or "benchmark_results" in data


# 10. Packaging & Wheel Build Verification Test
def test_package_build_and_metadata():
    """Verify python -m build generates sdist (.tar.gz) and wheel (.whl) cleanly."""
    res = subprocess.run([sys.executable, "-m", "build", "--wheel", "--sdist"], capture_output=True, text=True, timeout=60)
    assert res.returncode == 0
    dist_dir = Path("dist")
    assert dist_dir.exists()
    wheels = list(dist_dir.glob("*.whl"))
    sdists = list(dist_dir.glob("*.tar.gz"))
    assert len(wheels) >= 1
    assert len(sdists) >= 1
