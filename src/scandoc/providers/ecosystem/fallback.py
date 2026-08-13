"""
ProviderFallbackEngine managing provider fallback chains, user overrides, and privacy policies.
"""

import logging
from typing import List, Optional, Tuple

from scandoc.agent.taxonomy import Capability, PrivacyPolicy
from scandoc.providers.ecosystem.exceptions import ProviderNotFoundError
from scandoc.providers.ecosystem.models import FallbackTrace, ProviderDescriptor, UserProviderConfig
from scandoc.providers.ecosystem.registry import ProviderRegistry, default_provider_registry
from scandoc.providers.ecosystem.taxonomy import ProviderHealthState

logger = logging.getLogger("scandoc.providers.ecosystem.fallback")


class ProviderFallbackEngine:
    """
    Executes provider selection and fallback chains obeying user overrides, priorities, and privacy policy.
    """

    def __init__(self, registry: Optional[ProviderRegistry] = None):
        self._registry = registry or default_provider_registry

    def select_provider_with_fallback(
        self,
        capability: Capability,
        user_config: Optional[UserProviderConfig] = None,
        privacy_policy: PrivacyPolicy = PrivacyPolicy.LOCAL_PREFERRED,
        page_index: Optional[int] = None,
    ) -> Tuple[ProviderDescriptor, List[FallbackTrace]]:
        """
        Select best provider for capability obeying user overrides, priorities, and privacy constraints.
        Returns (selected_descriptor, fallback_traces).
        """
        traces: List[FallbackTrace] = []
        cfg = user_config or UserProviderConfig()

        # 1. Check Page-level or Global User Override
        override_id = None
        if page_index is not None and page_index in cfg.page_overrides:
            override_id = cfg.page_overrides[page_index].get(capability)
        if not override_id:
            override_id = cfg.overrides.get(capability)

        if override_id:
            try:
                desc = self._registry.get_descriptor(override_id)
                # Verify privacy constraint
                if privacy_policy == PrivacyPolicy.LOCAL_ONLY and desc.local_or_remote == "remote":
                    traces.append(
                        FallbackTrace(
                            task=capability.value,
                            attempt=1,
                            provider_id=override_id,
                            result="SKIPPED",
                            reason=f"User override '{override_id}' violates LOCAL_ONLY privacy policy",
                        )
                    )
                else:
                    traces.append(
                        FallbackTrace(
                            task=capability.value,
                            attempt=1,
                            provider_id=override_id,
                            result="SELECTED",
                            reason="Selected via explicit user override",
                        )
                    )
                    return desc, traces
            except ProviderNotFoundError:
                traces.append(
                    FallbackTrace(
                        task=capability.value,
                        attempt=1,
                        provider_id=override_id,
                        result="FAILED",
                        reason=f"User override provider '{override_id}' not found in registry",
                    )
                )

        # 2. Build Candidate Fallback Priority List
        candidates: List[str] = cfg.provider_priority.get(capability, [])
        if not candidates:
            # Default fallback candidates by capability
            if capability == Capability.OCR:
                candidates = ["ocr.rapidocr", "ocr.surya", "ocr.tesseract", "ocr.remote"]
            elif capability == Capability.LAYOUT:
                candidates = ["layout.rtdetr", "layout.yolo"]
            elif capability == Capability.TABLE:
                candidates = ["table.slanet"]
            elif capability == Capability.VLM:
                candidates = ["vlm.local", "vlm.huggingface", "vlm.remote"]
            else:
                candidates = [f"{capability.value}.local"]

        # 3. Evaluate Candidate Priority Chain
        attempt = len(traces) + 1
        for pid in candidates:
            try:
                desc = self._registry.get_descriptor(pid)
            except ProviderNotFoundError:
                traces.append(
                    FallbackTrace(
                        task=capability.value,
                        attempt=attempt,
                        provider_id=pid,
                        result="FAILED",
                        reason=f"Candidate provider '{pid}' not registered",
                    )
                )
                attempt += 1
                continue

            # Privacy filter check
            if privacy_policy == PrivacyPolicy.LOCAL_ONLY and desc.local_or_remote == "remote":
                traces.append(
                    FallbackTrace(
                        task=capability.value,
                        attempt=attempt,
                        provider_id=pid,
                        result="SKIPPED",
                        reason="Remote provider skipped under LOCAL_ONLY privacy policy",
                    )
                )
                attempt += 1
                continue

            if privacy_policy == PrivacyPolicy.REMOTE_ONLY and desc.local_or_remote == "local":
                traces.append(
                    FallbackTrace(
                        task=capability.value,
                        attempt=attempt,
                        provider_id=pid,
                        result="SKIPPED",
                        reason="Local provider skipped under REMOTE_ONLY privacy policy",
                    )
                )
                attempt += 1
                continue

            # Check provider health
            health = self._registry.get_health(pid)
            if health.state != ProviderHealthState.AVAILABLE:
                traces.append(
                    FallbackTrace(
                        task=capability.value,
                        attempt=attempt,
                        provider_id=pid,
                        result="FAILED",
                        reason=f"Provider health check failed: {health.details}",
                    )
                )
                attempt += 1
                continue

            # Successfully selected candidate provider
            traces.append(
                FallbackTrace(
                    task=capability.value,
                    attempt=attempt,
                    provider_id=pid,
                    result="SELECTED",
                    reason=f"Provider '{pid}' selected via fallback chain evaluation",
                )
            )
            return desc, traces

        raise ProviderNotFoundError(f"No available provider found for capability '{capability.value}' under policy '{privacy_policy.value}'")
