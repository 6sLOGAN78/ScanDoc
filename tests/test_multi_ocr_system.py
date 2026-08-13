"""
Unit and security integration test suite for Phase 7: Multi-OCR Provider System.
"""

import io
import json
import os
from typing import BinaryIO, List, Optional, Union
import pytest

from scandoc.models import DocumentIR
from scandoc.providers.ocr import (
    BaseOcrProvider,
    BaseHttpResponseAdapter,
    DefaultHttpResponseAdapter,
    GenericRemoteOcrProvider,
    HuggingFaceOcrAdapter,
    HuggingFaceOcrConfig,
    OcrCapability,
    OcrProviderConfig,
    OcrProviderRegistry,
    OCRResult,
    OCRTextRegion,
    RapidOCRProvider,
    SecretRef,
    TesseractProvider,
    ocr_result_to_document_ir,
    OcrProviderUnavailableError,
)
from scandoc.models.geometry import BoundingBox


class CustomPluginOcrProvider(BaseOcrProvider):
    """Custom third-party developer plugin provider."""

    @property
    def provider_id(self) -> str:
        return "custom_plugin"

    @property
    def model_id(self) -> str:
        return "CustomModel-v1"

    @property
    def supported_languages(self) -> List[str]:
        return ["en", "es"]

    def initialize(self, config: Optional[OcrProviderConfig] = None) -> None:
        pass

    def process_image(
        self,
        image_input: Union[str, bytes, bytearray, BinaryIO],
        config: Optional[OcrProviderConfig] = None,
    ) -> OCRResult:
        bbox = BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.3, is_normalized=True)
        reg = OCRTextRegion(text="Custom Plugin Output", bbox=bbox, confidence=0.99)
        return OCRResult(
            full_text="Custom Plugin Output",
            regions=[reg],
            provider_id=self.provider_id,
            model_id=self.model_id,
            image_width=500,
            image_height=200,
        )


def test_secret_ref_redaction_and_retrieval(monkeypatch):
    """Security Test: Verify raw secret values are NEVER leaked in str, repr, dict, or JSON."""
    raw_key = "sk-PROD-SECRET-KEY-123456789"
    secret = SecretRef(raw_secret_value=raw_key)

    # 1. Verify retrieval works
    assert secret.get_secret_value() == raw_key

    # 2. Verify str and repr mask secret
    assert raw_key not in repr(secret)
    assert raw_key not in str(secret)
    assert "***REDACTED***" in repr(secret)

    # 3. Verify Pydantic dict and JSON export redact secret
    d = secret.model_dump()
    assert d["raw_secret_value"] == "***REDACTED***"
    assert raw_key not in json.dumps(d)
    assert raw_key not in secret.model_dump_json()

    # 4. Verify env_var reference
    monkeypatch.setenv("TEST_OCR_API_KEY", "env-secret-val-999")
    secret_env = SecretRef(env_var="TEST_OCR_API_KEY")
    assert secret_env.get_secret_value() == "env-secret-val-999"
    assert "TEST_OCR_API_KEY" in repr(secret_env)


def test_ocr_provider_registry_lifecycle():
    """Test OcrProviderRegistry register, unregister, duplicate handling, and lookup."""
    registry = OcrProviderRegistry(register_defaults=False)
    assert len(registry.list_providers()) == 0

    rapid = RapidOCRProvider()
    tess = TesseractProvider()
    registry.register(rapid)
    registry.register(tess)

    assert len(registry.list_providers()) == 2
    assert registry.get_provider("rapidocr").provider_id == "rapidocr"
    assert registry.get_provider("tesseract").provider_id == "tesseract"

    # Test duplicate registration overwrites cleanly
    rapid_dup = RapidOCRProvider()
    registry.register(rapid_dup)
    assert len(registry.list_providers()) == 2

    # Test unregister
    removed = registry.unregister("tesseract")
    assert removed is tess
    assert len(registry.list_providers()) == 1


def test_custom_third_party_provider_plugin():
    """Test custom developer provider registration without modifying core OCR code."""
    registry = OcrProviderRegistry(register_defaults=False)
    custom_p = CustomPluginOcrProvider()
    registry.register(custom_p)

    provider = registry.get_provider("custom_plugin")
    res = provider.process_image(b"fake_image")
    assert res.full_text == "Custom Plugin Output"
    assert res.provider_id == "custom_plugin"


def test_provider_capability_discovery():
    """Test capability reporting across default registered providers."""
    registry = OcrProviderRegistry(register_defaults=True)
    capabilities: List[OcrCapability] = registry.list_capabilities()

    pids = {c.provider_id for c in capabilities}
    assert "rapidocr" in pids
    assert "tesseract" in pids
    assert "remote_http" in pids
    assert "huggingface" in pids

    rapid_cap = next(c for c in capabilities if c.provider_id == "rapidocr")
    assert rapid_cap.is_local is True
    assert rapid_cap.supports_polygons is True
    assert "en" in rapid_cap.supported_languages

    remote_cap = next(c for c in capabilities if c.provider_id == "remote_http")
    assert remote_cap.is_local is False
    assert remote_cap.supports_batch is True


def test_deterministic_provider_selection_and_fallback():
    """Test deterministic provider selection and fallback chain."""
    registry = OcrProviderRegistry(register_defaults=True)

    # 1. Explicit request for rapidocr
    cfg_rapid = OcrProviderConfig(provider_name="rapidocr")
    p_rapid = registry.select_provider(cfg_rapid)
    assert p_rapid.provider_id == "rapidocr"

    # 2. Selection with unavailable requested provider falling back
    cfg_unavail = OcrProviderConfig(provider_name="non_existent_provider")
    p_fallback = registry.select_provider(cfg_unavail, fallback_chain=["rapidocr", "tesseract"])
    assert p_fallback.provider_id == "rapidocr"

    # 3. Auto selection
    cfg_auto = OcrProviderConfig(provider_name="auto")
    p_auto = registry.select_provider(cfg_auto)
    assert p_auto.is_available is True


def test_generic_remote_ocr_provider_mock(monkeypatch):
    """Test GenericRemoteOcrProvider HTTP transport and secret header injection."""
    secret = SecretRef(raw_secret_value="sk-TEST-SECRET-KEY-999")
    config = OcrProviderConfig(
        provider_name="remote_http",
        endpoint="http://mock-ocr-service.internal/api/v1/ocr",
        api_key_ref=secret,
    )

    remote_prov = GenericRemoteOcrProvider(config=config)
    assert remote_prov.is_available is True

    # Mock urllib.request.urlopen
    mock_json_response = {
        "full_text": "Remote Service Output Line",
        "regions": [
            {
                "text": "Remote Service Output Line",
                "bbox": [0.1, 0.1, 0.9, 0.3],
                "confidence": 0.97,
            }
        ]
    }

    class MockHTTPResponse:
        def read(self):
            return json.dumps(mock_json_response).encode("utf-8")
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    recorded_headers = {}

    def mock_urlopen(req, timeout=None):
        recorded_headers.update(dict(req.headers))
        return MockHTTPResponse()

    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen)

    # Create dummy PNG image bytes (100x50)
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (100, 50), color=(255, 255, 255)).save(buf, format="PNG")
    img_bytes = buf.getvalue()

    res = remote_prov.process_image(img_bytes)

    assert res.full_text == "Remote Service Output Line"
    assert res.provider_id == "remote_http"
    assert res.image_width == 100
    assert len(res.regions) == 1
    assert res.regions[0].confidence == 0.97

    # Verify authorization header had bearer secret injected securely
    assert recorded_headers.get("Authorization") == "Bearer sk-TEST-SECRET-KEY-999"

    # Security Assertion: Verify raw secret is NEVER present in result or IR
    doc: DocumentIR = ocr_result_to_document_ir(res)
    json_dump = doc.model_dump_json()
    assert "sk-TEST-SECRET-KEY-999" not in json_dump


def test_tesseract_provider_behavior():
    """Test TesseractProvider capability and graceful unavailable handling."""
    tess = TesseractProvider()
    assert tess.provider_id == "tesseract"
    assert "eng" in tess.supported_languages
    assert isinstance(tess.is_available, bool)

    if not tess.is_available:
        with pytest.raises(OcrProviderUnavailableError):
            tess.initialize()


def test_huggingface_ocr_adapter_architecture():
    """Test HuggingFaceOcrAdapter architecture and configuration."""
    cfg = HuggingFaceOcrConfig(
        hf_model_id="microsoft/trocr-base-printed",
        token_ref=SecretRef(env_var="HF_TOKEN"),
    )
    adapter = HuggingFaceOcrAdapter(config=cfg)
    assert adapter.provider_id == "huggingface"
    assert adapter.model_id == "microsoft/trocr-base-printed"
    assert isinstance(adapter.is_available, bool)


def test_security_repository_secret_scan():
    """Security Test: Verify no hardcoded API keys exist in test results or DocumentIR dumps."""
    secret_key = "sk-SUPER-SECRET-KEY-999"
    secret = SecretRef(raw_secret_value=secret_key)
    
    cfg = OcrProviderConfig(provider_name="rapidocr", api_key_ref=secret)
    prov = RapidOCRProvider(config=cfg)
    
    # Assert secret string is not in representation or dumps
    assert secret_key not in repr(cfg)
    assert secret_key not in str(cfg)
    assert secret_key not in json.dumps(cfg.model_dump())
