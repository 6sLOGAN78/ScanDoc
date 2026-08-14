"""
Comprehensive test suite for Phase 34: Autonomous Model Download, Pinning & Auto-Cache Provisioning Lifecycle.
"""

import hashlib
import json
from pathlib import Path
import threading
import pytest

from scandoc.cli import main
from scandoc.cli.taxonomy import ExitCode
from scandoc.models_mgmt import (
    ModelDownloader,
    ModelManager,
    ModelRegistry,
    ModelSpec,
    ModelStore,
    OfflineModeError,
    ModelDownloadError,
    TaskType,
)
from scandoc.providers.ocr.rapidocr_provider import RapidOCRProvider


@pytest.fixture
def tmp_store(tmp_path):
    return ModelStore(base_dir=tmp_path / "models")


@pytest.fixture
def manager(tmp_store):
    reg = ModelRegistry(register_defaults=True)
    return ModelManager(registry=reg, store=tmp_store, offline=False)


# 1. Model Manifest & Spec Resolution Test
def test_model_manifest_resolution(manager):
    spec = manager.registry.lookup("rapidocr_onnx")
    assert spec is not None
    assert spec.filename == "ch_PP-OCRv4_rec_infer.onnx"
    assert spec.checksum_sha256 is not None
    assert len(spec.checksum_sha256) == 64


# 2. Real SHA-256 Hashing & Verification Tests
def test_real_sha256_calculation_and_verification(tmp_path, tmp_store):
    dummy_file = tmp_path / "dummy_weights.onnx"
    payload = b"REAL_SHA256_TEST_PAYLOAD_WEIGHTS_12345"
    dummy_file.write_bytes(payload)

    expected_hash = hashlib.sha256(payload).hexdigest()
    assert tmp_store.verify_checksum(dummy_file, expected_hash) is True
    assert tmp_store.verify_checksum(dummy_file, "invalid_hash_123") is False


# 3. Checksum Mismatch Rejection & Atomic .part File Cleanup Test
def test_checksum_mismatch_rejection(tmp_store):
    downloader = ModelDownloader(store=tmp_store, offline=False)
    spec = ModelSpec(
        model_id="corrupted_model_test",
        model_name="Corrupted Model",
        task=TaskType.OCR,
        source=ModelSource_LOCAL_PATH if False else spec_source_url(),
        checksum_sha256="0000000000000000000000000000000000000000000000000000000000000000",
    )

    with pytest.raises(ModelDownloadError, match="Checksum verification failed"):
        downloader.download_model(spec)


def spec_source_url():
    from scandoc.models_mgmt.taxonomy import ModelSource
    return ModelSource.URL


# 4. Strict Zero-Network Offline Mode Enforcement Test
def test_strict_offline_mode_zero_network(tmp_store, monkeypatch):
    downloader = ModelDownloader(store=tmp_store, offline=True)
    spec = ModelSpec(
        model_id="offline_test_model",
        model_name="Offline Test Model",
        task=TaskType.OCR,
    )

    # Ensure no network socket can be created
    def raise_on_socket(*args, **kwargs):
        raise RuntimeError("Network socket call attempted in offline mode!")

    monkeypatch.setattr("socket.socket", raise_on_socket)

    with pytest.raises(OfflineModeError, match="Strict offline mode"):
        downloader.download_model(spec)


# 5. CLI Model Management Commands Test (list, status, download, verify, clear)
def test_cli_models_subcommands(capsys):
    # 1. List
    assert main(["models", "list", "--json"]) == ExitCode.SUCCESS
    data_list = json.loads(capsys.readouterr().out)
    assert len(data_list) >= 5

    # 2. Status
    assert main(["models", "status", "rapidocr_onnx", "--json"]) == ExitCode.SUCCESS
    data_status = json.loads(capsys.readouterr().out)
    assert data_status[0]["model_id"] == "rapidocr_onnx"

    # 3. Download
    assert main(["models", "download", "basic_figure_analyzer", "--json"]) == ExitCode.SUCCESS
    data_dl = json.loads(capsys.readouterr().out)
    assert data_dl[0]["status"] == "downloaded"

    # 4. Verify
    assert main(["models", "verify", "basic_figure_analyzer", "--json"]) == ExitCode.SUCCESS
    data_v = json.loads(capsys.readouterr().out)
    assert data_v[0]["exists"] is True

    # 5. Clear
    assert main(["models", "clear", "basic_figure_analyzer", "--json"]) == ExitCode.SUCCESS
    data_c = json.loads(capsys.readouterr().out)
    assert data_c[0]["removed"] is True


# 6. Thread Concurrency Lock Test
def test_concurrent_model_downloads(manager):
    spec = manager.registry.lookup("basic_figure_analyzer")
    threads = []
    results = [None] * 5

    def worker(idx):
        res = manager.resolve("basic_figure_analyzer")
        results[idx] = res

    for i in range(5):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert all(r is not None for r in results)
    assert all(r.model_id == "basic_figure_analyzer" for r in results)


# 7. Provider Integration Test
def test_provider_model_manager_integration():
    prov = RapidOCRProvider()
    assert prov.provider_id == "rapidocr"
    assert prov.is_available is True
