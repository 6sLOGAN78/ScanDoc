"""
Comprehensive test suite for Phase 26: Production Release Packaging & Release Tooling.
"""

from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
import pytest

import scandoc
from scandoc.cli import main
from scandoc.cli.taxonomy import ExitCode


# 1. Version Consistency Tests
def test_version_consistency():
    """Verify single authoritative version across package, __version__, and CLI."""
    assert scandoc.__version__ == "0.1.0"

    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists()
    content = pyproject_path.read_text(encoding="utf-8")
    assert 'version = "0.1.0"' in content


def test_cli_version_flag(capsys):
    """Verify `scandoc --version` outputs correct version."""
    ret = main(["--version"])
    assert ret == ExitCode.SUCCESS
    captured = capsys.readouterr()
    assert "0.1.0" in captured.out or "0.1.0" in captured.err


# 2. Package Discovery Tests for All Submodules
def test_package_submodule_discovery():
    """Verify all core packages/submodules are discovered and importable."""
    import scandoc.acceleration
    import scandoc.agent
    import scandoc.analysis
    import scandoc.benchmarks
    import scandoc.cli
    import scandoc.core
    import scandoc.exporters
    import scandoc.formats
    import scandoc.image
    import scandoc.ingestion
    import scandoc.models
    import scandoc.pdf
    import scandoc.pipelines
    import scandoc.providers
    import scandoc.server
    import scandoc.structure

    assert scandoc.cli.main is not None
    assert scandoc.server.create_app is not None
    assert scandoc.benchmarks.BenchmarkRunner is not None


# 3. Production Build & Artifact Validation Tests
def test_production_build_wheels_and_sdists():
    """Verify python -m build produces valid .whl and .tar.gz without errors."""
    res = subprocess.run([sys.executable, "-m", "build"], capture_output=True, text=True, timeout=60)
    assert res.returncode == 0

    dist_dir = Path("dist")
    assert dist_dir.exists()

    wheels = list(dist_dir.glob("*.whl"))
    sdists = list(dist_dir.glob("*.tar.gz"))

    assert len(wheels) >= 1
    assert len(sdists) >= 1

    wheel_file = wheels[0]
    sdist_file = sdists[0]

    # Package Size Sanity Check: Wheel & Sdist must be under 2MB (no model weights or caches)
    assert wheel_file.stat().st_size < 2000000  # < 2 MB
    assert sdist_file.stat().st_size < 2000000  # < 2 MB

    # Inspect Wheel zip contents: verify no tests, .env files, secrets, or model weights
    with zipfile.ZipFile(wheel_file, "r") as z:
        names = z.namelist()
        assert any(n.startswith("scandoc/") for n in names)
        assert not any(n.startswith("tests/") for n in names)
        assert not any(n.endswith(".onnx") or n.endswith(".bin") or n.endswith(".pt") for n in names)
        assert not any(n.endswith(".env") or n.endswith(".pem") or n.endswith(".key") for n in names)


# 4. Twine Package Metadata Validation Test
def test_twine_metadata_validation():
    """Verify package wheel metadata using twine check if available."""
    twine_bin = shutil.which("twine")
    if twine_bin:
        res = subprocess.run([twine_bin, "check", "dist/*"], capture_output=True, text=True, timeout=30)
        assert res.returncode == 0
        assert "PASSED" in res.stdout or "PASSED" in res.stderr or res.returncode == 0
    else:
        pytest.skip("twine executable not present in environment")


# 5. Secret & Credential Exclusion Scan Test
def test_secret_and_credential_exclusion_scan():
    """Scan source codebase to ensure zero credentials or hardcoded API keys exist."""
    forbidden_tokens = ["sk-proj-", "hf_token_secret_", "AWS_SECRET_ACCESS_KEY="]
    src_dir = Path("src")

    for py_file in src_dir.glob("**/*.py"):
        content = py_file.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in content, f"Forbidden credential token '{token}' found in '{py_file}'"


# 6. CLI Smoke Tests Across All Subcommands
def test_cli_subcommands_smoke(capsys):
    """Verify help commands for all CLI subcommands."""
    assert main(["--help"]) == ExitCode.SUCCESS
    assert main(["convert", "--help"]) == ExitCode.SUCCESS
    assert main(["inspect", "--help"]) == ExitCode.SUCCESS
    assert main(["serve", "--help"]) == ExitCode.SUCCESS
    assert main(["benchmark", "--help"]) == ExitCode.SUCCESS
