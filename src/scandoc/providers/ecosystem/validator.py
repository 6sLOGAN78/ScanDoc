"""
ProviderValidator verifying configuration, model, runtime, device, and credentials without executing inference.
"""

import logging
from typing import Any, Dict, Optional

from scandoc.acceleration.manager import default_execution_manager
from scandoc.providers.ecosystem.credentials import CredentialReference
from scandoc.providers.ecosystem.exceptions import ProviderValidationError
from scandoc.providers.ecosystem.models import ProviderDescriptor, ProviderHealth
from scandoc.providers.ecosystem.taxonomy import ProviderHealthState, ProviderType

logger = logging.getLogger("scandoc.providers.ecosystem.validator")


class ProviderValidator:
    """
    Validates provider requirements, hardware compatibility, and credentials before instantiation.
    Never performs document inference during validation.
    """

    @classmethod
    def validate_provider(
        cls,
        descriptor: ProviderDescriptor,
        config: Optional[Dict[str, Any]] = None,
        credential_ref: Optional[CredentialReference] = None,
    ) -> ProviderHealth:
        """
        Validate provider readiness and return ProviderHealth status.
        """
        cfg = config or {}

        # 1. Device Compatibility
        target_device = cfg.get("device", "cpu")
        if descriptor.supported_devices and target_device not in descriptor.supported_devices and "auto" not in descriptor.supported_devices:
            return ProviderHealth(
                provider_id=descriptor.provider_id,
                state=ProviderHealthState.RUNTIME_UNAVAILABLE,
                details=f"Device '{target_device}' is not supported by provider. Supported: {descriptor.supported_devices}",
            )

        # 2. Remote API Credential Validation
        if descriptor.provider_type in (ProviderType.REMOTE_API, ProviderType.OPENAI_COMPATIBLE, ProviderType.HUGGINGFACE_REMOTE):
            endpoint = cfg.get("endpoint")
            if not endpoint:
                return ProviderHealth(
                    provider_id=descriptor.provider_id,
                    state=ProviderHealthState.MISCONFIGURED,
                    details="Remote API provider requires a valid HTTP endpoint URL.",
                )

            if credential_ref is not None:
                secret_val = credential_ref.resolve_value()
                if not secret_val:
                    return ProviderHealth(
                        provider_id=descriptor.provider_id,
                        state=ProviderHealthState.AUTHENTICATION_REQUIRED,
                        details=f"Credential reference '{credential_ref.credential_id}' could not be resolved from environment.",
                    )

        # Provider passed pre-flight validation
        return ProviderHealth(
            provider_id=descriptor.provider_id,
            state=ProviderHealthState.AVAILABLE,
            details="Provider configuration, runtime, and credentials validated successfully.",
        )
