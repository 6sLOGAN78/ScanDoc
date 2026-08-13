"""
Unit and integration test suite for Phase 17: Multi-Provider Ecosystem & User-Configurable Providers.
"""

import os
import pytest

from scandoc.agent.taxonomy import Capability, PrivacyPolicy
from scandoc.providers.ecosystem import (
    CredentialReference,
    FallbackTrace,
    ProviderDescriptor,
    ProviderFactory,
    ProviderFallbackEngine,
    ProviderHealth,
    ProviderHealthState,
    ProviderNotFoundError,
    ProviderRegistry,
    ProviderType,
    ProviderValidator,
    UserProviderConfig,
)
from scandoc.providers.ocr.rapidocr_provider import RapidOCRProvider


def test_provider_registry_discovery_and_lookup():
    """Test ProviderRegistry descriptor registration, discovery, and capability lookups."""
    reg = ProviderRegistry(register_builtins=True)

    # Built-in OCR provider lookup
    desc = reg.get_descriptor("ocr.rapidocr")
    assert desc.provider_id == "ocr.rapidocr"
    assert desc.capability == Capability.OCR
    assert desc.provider_type == ProviderType.LOCAL

    # Filter descriptors by capability
    ocr_descs = reg.list_descriptors(capability=Capability.OCR)
    assert len(ocr_descs) >= 3


def test_credential_reference_resolution_and_redaction():
    """Security Test: CredentialReference resolves secret from environment without exposing key in string representation."""
    os.environ["SCANDOC_TEST_API_KEY"] = "sk-secret-token-9999"
    try:
        ref = CredentialReference(
            credential_id="remote_ocr_key",
            source_type="env",
            env_var_name="SCANDOC_TEST_API_KEY",
        )
        assert ref.resolve_value() == "sk-secret-token-9999"
        # Secret string representation must never contain raw API key
        assert "sk-secret-token-9999" not in str(ref)
        assert "sk-secret-token-9999" not in repr(ref)
    finally:
        os.environ.pop("SCANDOC_TEST_API_KEY", None)


def test_provider_validator_and_factory():
    """Test ProviderValidator pre-flight validation and ProviderFactory instantiation."""
    desc = ProviderDescriptor(
        provider_id="ocr.rapidocr",
        name="RapidOCR Local Engine",
        capability=Capability.OCR,
        provider_type=ProviderType.LOCAL,
        supported_devices=["cpu", "cuda"],
    )

    health = ProviderValidator.validate_provider(desc, config={"device": "cpu"})
    assert health.state == ProviderHealthState.AVAILABLE

    instance = ProviderFactory.create_provider(RapidOCRProvider, desc, config={"device": "cpu"})
    assert isinstance(instance, RapidOCRProvider)


def test_provider_fallback_engine_and_privacy_policy():
    """Test ProviderFallbackEngine user priority chains, overrides, and privacy enforcement."""
    engine = ProviderFallbackEngine()

    # LOCAL_ONLY policy must skip ocr.remote
    cfg = UserProviderConfig(
        provider_priority={Capability.OCR: ["ocr.remote", "ocr.rapidocr"]}
    )

    desc, traces = engine.select_provider_with_fallback(
        capability=Capability.OCR,
        user_config=cfg,
        privacy_policy=PrivacyPolicy.LOCAL_ONLY,
    )

    assert desc.provider_id == "ocr.rapidocr"
    assert len(traces) == 2
    assert traces[0].provider_id == "ocr.remote"
    assert traces[0].result == "SKIPPED"
    assert traces[1].provider_id == "ocr.rapidocr"
    assert traces[1].result == "SELECTED"


def test_user_page_override_priority():
    """Test explicit page-level user overrides in ProviderFallbackEngine."""
    engine = ProviderFallbackEngine()
    cfg = UserProviderConfig(
        overrides={Capability.OCR: "ocr.rapidocr"},
        page_overrides={2: {Capability.OCR: "ocr.surya"}},
    )

    # Page 0 uses global override (ocr.rapidocr)
    desc_p0, _ = engine.select_provider_with_fallback(Capability.OCR, user_config=cfg, page_index=0)
    assert desc_p0.provider_id == "ocr.rapidocr"

    # Page 2 uses page-level override (ocr.surya)
    desc_p2, _ = engine.select_provider_with_fallback(Capability.OCR, user_config=cfg, page_index=2)
    assert desc_p2.provider_id == "ocr.surya"
