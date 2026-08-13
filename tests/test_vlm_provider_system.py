"""
Unit and integration test suite for Phase 15: VLM Provider System & Local Vision-Language Runtime.
"""

import json
import pytest

from scandoc.models import DocumentIR, DocumentMetadata
from scandoc.models.geometry import BoundingBox
from scandoc.providers.ocr.secrets import SecretRef
from scandoc.providers.vlm import (
    BaseVlmProvider,
    GenericRemoteVlmProvider,
    HuggingFaceVlmAdapter,
    LocalVlmProvider,
    OpenAiCompatibleVlmProvider,
    PrivacyViolationError,
    ProviderType,
    VlmConfig,
    VlmDocumentAdapter,
    VlmExecutionMode,
    VlmOutputValidationError,
    VlmOutputValidator,
    VlmProviderRegistry,
    VlmProviderUnavailableError,
    VlmRequest,
    VlmResult,
    VlmTaskType,
)


def test_vlm_request_and_result_schemas():
    """Test VlmRequest and VlmResult data model validation."""
    req = VlmRequest(
        task=VlmTaskType.TABLE_UNDERSTANDING,
        prompt="Extract markdown table structure from image.",
        output_format="json",
    )
    assert req.task == VlmTaskType.TABLE_UNDERSTANDING

    res = VlmResult(
        task=VlmTaskType.TABLE_UNDERSTANDING,
        text_result='{"rows": 2, "cols": 2}',
        structured_result={"rows": 2, "cols": 2},
        confidence=0.95,
        provider_id="local_vlm_engine",
        model_id="Qwen2-VL-7B-Instruct",
        execution_mode=VlmExecutionMode.LOCAL,
        device="cpu",
    )
    assert res.confidence == 0.95
    assert res.execution_mode == VlmExecutionMode.LOCAL


def test_local_vlm_provider_analysis():
    """Test LocalVlmProvider local multimodal analysis and structured output generation."""
    prov = LocalVlmProvider()
    req = VlmRequest(
        task=VlmTaskType.PAGE_UNDERSTANDING,
        prompt="Analyze page layout.",
        output_format="json",
    )
    res = prov.analyze(req)

    assert isinstance(res, VlmResult)
    assert res.provider_id == "local_vlm_engine"
    assert res.structured_result is not None
    assert "summary" in res.structured_result


def test_privacy_remote_vlm_enforcement():
    """Security Test: Generic and OpenAI remote VLM providers MUST raise PrivacyViolationError if allow_remote=False."""
    remote_p = GenericRemoteVlmProvider(
        config=VlmConfig(
            endpoint="https://api.vlm-cloud.internal/v1/analyze",
            allow_remote=False,
        )
    )
    openai_p = OpenAiCompatibleVlmProvider(
        config=VlmConfig(
            endpoint="https://api.openai.com/v1",
            api_key_ref=SecretRef(raw_secret_value="sk-secret-key-12345"),
            allow_remote=False,
        )
    )

    req = VlmRequest(prompt="Analyze visual figure.")

    with pytest.raises(PrivacyViolationError):
        remote_p.initialize()

    with pytest.raises(PrivacyViolationError):
        remote_p.analyze(req)

    with pytest.raises(PrivacyViolationError):
        openai_p.analyze(req)


def test_vlm_output_validator():
    """Test VlmOutputValidator validating valid JSON and rejecting malformed text."""
    valid_text = '```json\n{"status": "ok", "items": [1, 2]}\n```'
    parsed = VlmOutputValidator.validate_json(valid_text)
    assert parsed["status"] == "ok"
    assert VlmOutputValidator.validate_schema(parsed, ["status", "items"]) is True

    malformed_text = "This is not valid JSON text"
    with pytest.raises(VlmOutputValidationError):
        VlmOutputValidator.validate_json(malformed_text)

    with pytest.raises(VlmOutputValidationError):
        VlmOutputValidator.validate_schema(parsed, ["status", "missing_key"])


def test_vlm_provider_registry():
    """Test VlmProviderRegistry provider registration and privacy selection."""
    reg = VlmProviderRegistry(register_defaults=True)
    assert len(reg.list_providers()) == 4

    local_p = reg.select_provider(VlmConfig(allow_remote=False))
    assert local_p.provider_type == ProviderType.LOCAL


def test_vlm_streaming_interface():
    """Test VLM streaming tokens interface."""
    prov = LocalVlmProvider()
    req = VlmRequest(prompt="Stream analysis tokens.", output_format="text")
    tokens = list(prov.analyze_stream(req))

    assert len(tokens) >= 1
    assert "VLM Analysis" in tokens[0]
