"""
Unit and integration test suite for Phase 14: Model Management & Local Model Runtime.
"""

import hashlib
from pathlib import Path
import tempfile
import pytest

from scandoc.models_mgmt import (
    DEFAULT_MODEL_DIR,
    BaseModelLoader,
    DefaultOnnxModelLoader,
    InsufficientDiskSpaceError,
    LoadedModelCache,
    ModelDownloader,
    ModelFormat,
    ModelLoadError,
    ModelManager,
    ModelNotFoundError,
    ModelRegistry,
    ModelSource,
    ModelState,
    ModelSpec,
    ModelStore,
    ModelValidationError,
    ModelValidator,
    OfflineModeError,
    QuantizationType,
    TaskType,
)


def test_modelspec_schema_validation():
    """Test ModelSpec data model validation."""
    spec = ModelSpec(
        model_id="test_org/test_model",
        model_name="Test Model",
        task=TaskType.OCR,
        format=ModelFormat.ONNX,
        source=ModelSource.HUGGINGFACE,
        quantization=QuantizationType.INT8,
    )
    assert spec.model_id == "test_org/test_model"
    assert spec.task == TaskType.OCR
    assert spec.quantization == QuantizationType.INT8


def test_model_registry_lifecycle():
    """Test ModelRegistry register, unregister, lookup, and task filtering."""
    reg = ModelRegistry(register_defaults=False)
    spec = ModelSpec(
        model_id="slanet_table",
        model_name="SLANet Table Recognizer",
        task=TaskType.TABLE,
    )
    reg.register(spec)

    assert len(reg.list_models()) == 1
    assert reg.lookup("slanet_table") is not None
    assert len(reg.list_models(TaskType.TABLE)) == 1
    assert len(reg.list_models(TaskType.OCR)) == 0

    reg.unregister("slanet_table")
    assert reg.lookup("slanet_table") is None


def test_model_store_directory_hierarchy_and_size():
    """Test ModelStore directory creation, path determination, and size calculation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = ModelStore(base_dir=Path(tmp_dir))
        assert (Path(tmp_dir) / "ocr").exists()
        assert (Path(tmp_dir) / "table").exists()

        spec = ModelSpec(
            model_id="test_ocr_v1",
            model_name="Test OCR Model",
            task=TaskType.OCR,
        )
        meta_file = store.write_metadata(spec)
        assert meta_file.exists()

        size = store.calculate_size(meta_file.parent)
        assert size > 0

        read_spec = store.get_model_spec("test_ocr_v1")
        assert read_spec is not None
        assert read_spec.model_name == "Test OCR Model"


def test_sha256_checksum_verification():
    """Test SHA-256 cryptographic checksum verification."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = ModelStore(base_dir=Path(tmp_dir))
        file_path = Path(tmp_dir) / "weights.onnx"
        payload = b"SAMPLE_MODEL_WEIGHTS_CONTENT"
        file_path.write_bytes(payload)

        expected_hash = hashlib.sha256(payload).hexdigest()
        assert store.verify_checksum(file_path, expected_hash) is True
        assert store.verify_checksum(file_path, "invalid_checksum") is False


def test_offline_mode_enforcement():
    """Security Test: ModelDownloader MUST raise OfflineModeError when offline=True."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = ModelStore(base_dir=Path(tmp_dir))
        downloader = ModelDownloader(store=store, offline=True)
        spec = ModelSpec(
            model_id="hf_org/remote_model",
            model_name="Remote HF Model",
            source=ModelSource.HUGGINGFACE,
        )

        with pytest.raises(OfflineModeError):
            downloader.download_model(spec)


def test_insufficient_disk_space_error():
    """Test InsufficientDiskSpaceError when required bytes exceeds available volume space."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = ModelStore(base_dir=Path(tmp_dir))
        downloader = ModelDownloader(store=store, offline=False)

        # Require 1000 Terabytes
        huge_bytes = 1000 * 1024 * 1024 * 1024 * 1024

        with pytest.raises(InsufficientDiskSpaceError):
            downloader.check_disk_space(Path(tmp_dir), huge_bytes)


def test_model_validator_integrity_and_hardware_compatibility():
    """Test ModelValidator checking local path, SHA-256 checksums, and hardware capabilities."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = ModelStore(base_dir=Path(tmp_dir))
        p = Path(tmp_dir) / "model_dir"
        p.mkdir()
        w = p / "model.onnx"
        payload = b"VALID_WEIGHTS"
        w.write_bytes(payload)
        sha = hashlib.sha256(payload).hexdigest()

        spec = ModelSpec(
            model_id="valid_model",
            model_name="Valid Model",
            local_path=str(p),
            checksum_sha256=sha,
            supported_devices=["cpu"],
        )

        val_res = ModelValidator.validate(spec, store)
        assert val_res.is_valid is True
        assert val_res.checksum_verified is True
        assert val_res.hardware_compatible is True


def test_loaded_model_cache_and_lru_eviction():
    """Test LoadedModelCache LRU eviction and memory bounds."""
    cache = LoadedModelCache(max_models=2)
    cache.put("model_1", "<SESSION_1>", memory_bytes=100)
    cache.put("model_2", "<SESSION_2>", memory_bytes=100)

    assert cache.get("model_1") == "<SESSION_1>"
    assert cache.get("model_2") == "<SESSION_2>"

    # Adding 3rd model triggers LRU eviction of oldest
    cache.put("model_3", "<SESSION_3>", memory_bytes=100)
    assert cache.get("model_1") is None
    assert cache.get("model_3") == "<SESSION_3>"


def test_model_manager_resolve_and_load_flow():
    """Test full ModelManager resolve, acquisition, validation, loading, and cache workflow."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = ModelStore(base_dir=Path(tmp_dir))
        manager = ModelManager(store=store, offline=False)

        spec = ModelSpec(
            model_id="slanet_v1",
            model_name="SLANet Table Recognizer",
            task=TaskType.TABLE,
            source=ModelSource.LOCAL_PATH,
        )
        manager.registry.register(spec)

        session = manager.load_model("slanet_v1", device="cpu")
        assert session is not None
        assert manager.registry.lookup("slanet_v1").state == ModelState.LOADED

        manager.unload_model("slanet_v1")
        assert manager.registry.lookup("slanet_v1").state == ModelState.READY
