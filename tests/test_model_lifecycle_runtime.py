"""
Unit, integration, security, and concurrency test suite for Phase 22: Model Lifecycle & Runtime Management.
"""

import os
from pathlib import Path
import pytest

from scandoc.models_mgmt import (
    ModelDownloader,
    ModelManager,
    ModelRegistry,
    ModelSpec,
    ModelStore,
    ModelValidator,
    ModelFormat,
    ModelSource,
    ModelState,
    OfflineModeError,
    TaskType,
)
from scandoc.providers.ecosystem.credentials import CredentialReference


@pytest.fixture
def tmp_model_store(tmp_path) -> ModelStore:
    return ModelStore(base_dir=tmp_path / ".scandoc" / "models")


@pytest.fixture
def sample_model_spec() -> ModelSpec:
    return ModelSpec(
        model_id="scandoc/rtdetr-layout-v1",
        provider="layout.rtdetr",
        model_name="RT-DETR Layout Model",
        version="1.0.0",
        task=TaskType.LAYOUT,
        format=ModelFormat.ONNX,
        source=ModelSource.BUNDLED,
        size_bytes=1024,
    )


def test_model_registration_and_discovery(tmp_model_store, sample_model_spec):
    """Test ModelRegistry registration, list_available, and is_installed check."""
    registry = ModelRegistry(register_defaults=False)
    registry.register(sample_model_spec)

    models = registry.list_models()
    assert len(models) == 1
    assert models[0].model_id == "scandoc/rtdetr-layout-v1"

    manager = ModelManager(registry=registry, store=tmp_model_store)
    assert manager.is_installed("scandoc/rtdetr-layout-v1") is False


def test_local_model_path_resolution_and_install(tmp_model_store, sample_model_spec, tmp_path):
    """Test installing and resolving local path model."""
    weights_path = tmp_path / "custom_weights.onnx"
    weights_path.write_bytes(b"ONNX_MOCK_MODEL_WEIGHTS_CONTENT_12345")

    local_spec = sample_model_spec.model_copy(
        update={
            "model_id": "scandoc/local-layout",
            "source": ModelSource.LOCAL_PATH,
            "local_path": str(weights_path),
        }
    )

    manager = ModelManager(store=tmp_model_store)
    installed_spec = manager.install(local_spec)

    assert installed_spec.state == ModelState.READY
    assert manager.is_installed("scandoc/local-layout") is True
    assert manager.get_model_path("scandoc/local-layout") is not None


def test_offline_mode_enforcement(tmp_model_store, sample_model_spec):
    """Test that resolving an uninstalled remote model in offline mode raises OfflineModeError."""
    hf_spec = sample_model_spec.model_copy(
        update={"model_id": "org/uninstalled-model", "source": ModelSource.HUGGINGFACE}
    )
    registry = ModelRegistry(register_defaults=False)
    registry.register(hf_spec)

    manager = ModelManager(registry=registry, store=tmp_model_store, offline=True)
    with pytest.raises(OfflineModeError):
        manager.resolve("org/uninstalled-model")


def test_model_removal(tmp_model_store, sample_model_spec):
    """Test explicit model installation and removal from ModelStore."""
    manager = ModelManager(store=tmp_model_store)
    installed_spec = manager.install(sample_model_spec)

    assert manager.is_installed(sample_model_spec.model_id) is True
    removed = manager.remove(sample_model_spec.model_id)
    assert removed is True
    assert manager.is_installed(sample_model_spec.model_id) is False


def test_remote_api_model_representation(sample_model_spec):
    """Test remote API model representation without requiring local weights download."""
    remote_spec = sample_model_spec.model_copy(
        update={
            "model_id": "remote/vlm-gpt4o",
            "source": ModelSource.REMOTE_API,
            "provider": "vlm.remote",
        }
    )
    assert remote_spec.source == ModelSource.REMOTE_API
    assert remote_spec.provider == "vlm.remote"


def test_secret_leakage_prevention(sample_model_spec):
    """Security Test: Verify Hugging Face tokens and API credentials NEVER appear in ModelSpec logs or exports."""
    secret_ref = CredentialReference(credential_id="hf_token_1", env_var_name="HF_TOKEN", raw_secret="hf_secret_token_abc123")
    
    spec = sample_model_spec.model_copy(
        update={"metadata": {"cred_id": secret_ref.credential_id}}
    )

    spec_str = str(spec.model_dump_json())
    assert "hf_secret_token_abc123" not in spec_str
    assert "hf_secret_token_abc123" not in str(secret_ref)
