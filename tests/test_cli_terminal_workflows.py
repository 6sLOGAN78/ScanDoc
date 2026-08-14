"""
Comprehensive test suite for Phase 23: CLI & Terminal Workflows.
"""

import json
from pathlib import Path
import time
import pytest

from scandoc.cli import main, create_parser
from scandoc.cli.taxonomy import ExitCode
from scandoc.exporters import default_exporter_registry
from scandoc.pipelines import DocumentPipeline, PipelineConfig


from fixtures.pdf_fixtures import generate_digital_pdf_bytes


@pytest.fixture
def sample_pdf_file(tmp_path) -> Path:
    p = tmp_path / "sample_doc.pdf"
    p.write_bytes(generate_digital_pdf_bytes())
    return p


@pytest.fixture
def sample_doc_dir(tmp_path) -> Path:
    d = tmp_path / "documents"
    d.mkdir()
    (d / "doc1.pdf").write_bytes(generate_digital_pdf_bytes(text="Doc 1 Content"))
    (d / "doc2.pdf").write_bytes(generate_digital_pdf_bytes(text="Doc 2 Content"))
    return d


def test_cli_help_and_version(capsys):
    """Test `scandoc --help` and main entry point with empty args."""
    ret = main([])
    assert ret == ExitCode.SUCCESS

    ret_help = main(["--help"])
    assert ret_help == ExitCode.SUCCESS
    captured = capsys.readouterr()
    assert "scandoc" in captured.out.lower() or "usage:" in captured.out.lower()


def test_cli_convert_single_file(sample_pdf_file, tmp_path):
    """Test `scandoc convert document.pdf --output result.md`."""
    out_file = tmp_path / "result.md"
    ret = main(["convert", str(sample_pdf_file), "--output", str(out_file), "--format", "markdown"])
    assert ret == ExitCode.SUCCESS
    assert out_file.exists()
    assert len(out_file.read_text()) > 0


def test_cli_convert_formats(sample_pdf_file, tmp_path):
    """Test `scandoc convert` across markdown, html, json, text, and docx formats."""
    for fmt in ["markdown", "html", "json", "text", "docx"]:
        out_file = tmp_path / f"result.{fmt}"
        ret = main(["convert", str(sample_pdf_file), "-o", str(out_file), "-f", fmt])
        assert ret == ExitCode.SUCCESS
        assert out_file.exists()


def test_cli_convert_directory_and_batch(sample_doc_dir, tmp_path):
    """Test `scandoc convert ./documents --output-dir ./output`."""
    out_dir = tmp_path / "output"
    ret = main(["convert", str(sample_doc_dir), "--output-dir", str(out_dir), "--format", "markdown"])
    assert ret == ExitCode.SUCCESS
    assert (out_dir / "doc1.md").exists()
    assert (out_dir / "doc2.md").exists()


def test_cli_convert_invalid_format(sample_pdf_file):
    """Test `scandoc convert` with invalid format returns ExitCode.CONFIGURATION_ERROR."""
    ret = main(["convert", str(sample_pdf_file), "--format", "invalid_format_xyz"])
    assert ret == ExitCode.CONFIGURATION_ERROR


def test_cli_convert_missing_input(tmp_path):
    """Test `scandoc convert` with non-existent file returns ExitCode.INPUT_ERROR."""
    missing = tmp_path / "non_existent.pdf"
    ret = main(["convert", str(missing)])
    assert ret == ExitCode.INPUT_ERROR


def test_cli_inspect_text_and_json(sample_pdf_file, capsys):
    """Test `scandoc inspect <file>` text and `--json` outputs."""
    ret = main(["inspect", str(sample_pdf_file)])
    assert ret == ExitCode.SUCCESS
    capsys.readouterr()  # Clear stdout buffer

    ret_json = main(["inspect", str(sample_pdf_file), "--json"])
    assert ret_json == ExitCode.SUCCESS
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["file_name"] == "sample_doc.pdf"
    assert "page_count" in data


def test_cli_benchmark(capsys):
    """Test `scandoc benchmark` execution."""
    ret = main(["benchmark", "-n", "5", "--workers", "2"])
    assert ret == ExitCode.SUCCESS
    capsys.readouterr()  # Clear stdout buffer

    ret_json = main(["benchmark", "-n", "5", "--workers", "2", "--json"])
    assert ret_json == ExitCode.SUCCESS
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "benchmark_results" in data


def test_cli_serve(capsys):
    """Test `scandoc serve` startup diagnostics."""
    ret = main(["serve", "--port", "8080", "--json"])
    assert ret == ExitCode.SUCCESS
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["port"] == 8080
    assert data["status"] == "active"


def test_cli_verbose_and_quiet_modes(sample_pdf_file, tmp_path, capsys):
    """Test `--verbose` and `--quiet` CLI options."""
    out_file = tmp_path / "out_v.md"
    ret_verbose = main(["convert", str(sample_pdf_file), "-o", str(out_file), "--verbose"])
    assert ret_verbose == ExitCode.SUCCESS

    out_file_q = tmp_path / "out_q.md"
    ret_quiet = main(["convert", str(sample_pdf_file), "-o", str(out_file_q), "--quiet"])
    assert ret_quiet == ExitCode.SUCCESS


def test_cli_secret_redaction(capsys):
    """Security Test: Verify API keys and tokens are never printed in CLI error diagnostics."""
    secret_str = "hf_token_secret_12345_key"
    ret = main(["convert", secret_str])
    assert ret == ExitCode.INPUT_ERROR
    captured = capsys.readouterr()
    assert secret_str not in captured.err
    assert secret_str not in captured.out


def test_cli_performance_overhead(sample_pdf_file):
    """Benchmark CLI invocation overhead versus direct pipeline call."""
    # Direct pipeline execution
    pipeline = DocumentPipeline(config=PipelineConfig(max_workers=1))
    t0 = time.perf_counter()
    for _ in range(5):
        pipeline.process(sample_pdf_file)
    direct_time = time.perf_counter() - t0

    # CLI execution
    t2 = time.perf_counter()
    for _ in range(5):
        main(["convert", str(sample_pdf_file), "--quiet", "--overwrite"])
    cli_time = time.perf_counter() - t2

    overhead_sec = cli_time - direct_time
    assert overhead_sec < 1.0  # CLI overhead must be less than 1.0 second for 5 calls
