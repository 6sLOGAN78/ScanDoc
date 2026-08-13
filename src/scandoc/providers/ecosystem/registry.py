"""
Central ProviderRegistry for provider discovery, lookup, capability queries, and health status monitoring.
"""

import logging
from typing import Dict, List, Optional, Tuple

from scandoc.agent.taxonomy import Capability, PrivacyPolicy
from scandoc.providers.ecosystem.exceptions import ProviderNotFoundError
from scandoc.providers.ecosystem.models import ProviderDescriptor, ProviderHealth
from scandoc.providers.ecosystem.taxonomy import ProviderHealthState, ProviderType
from scandoc.providers.ecosystem.validator import ProviderValidator

logger = logging.getLogger("scandoc.providers.ecosystem.registry")


class ProviderRegistry:
    """
    Central ProviderRegistry managing all registered scanDOC providers.
    Supports deterministic provider discovery, capability lookup, and privacy filtering.
    """

    def __init__(self, register_builtins: bool = True):
        self._descriptors: Dict[str, ProviderDescriptor] = {}
        self._instances: Dict[str, Any] = {}
        if register_builtins:
            self._register_builtin_descriptors()

    def _register_builtin_descriptors(self) -> None:
        builtins = [
            # OCR Providers
            ProviderDescriptor(
                provider_id="ocr.rapidocr",
                name="RapidOCR Local ONNX Engine",
                version="1.0.0",
                capability=Capability.OCR,
                provider_type=ProviderType.LOCAL,
                supported_devices=["cpu", "cuda", "auto"],
                supported_runtimes=["onnxruntime"],
                privacy_classification="private",
            ),
            ProviderDescriptor(
                provider_id="ocr.tesseract",
                name="Tesseract OCR Engine",
                version="5.0.0",
                capability=Capability.OCR,
                provider_type=ProviderType.LOCAL,
                supported_devices=["cpu"],
                supported_runtimes=["native"],
                privacy_classification="private",
            ),
            ProviderDescriptor(
                provider_id="ocr.surya",
                name="Surya OCR Engine",
                version="0.4.0",
                capability=Capability.OCR,
                provider_type=ProviderType.LOCAL,
                supported_devices=["cpu", "cuda"],
                supported_runtimes=["torch"],
                privacy_classification="private",
            ),
            ProviderDescriptor(
                provider_id="ocr.remote",
                name="Generic Remote OCR Service",
                version="1.0.0",
                capability=Capability.OCR,
                provider_type=ProviderType.REMOTE_API,
                supported_devices=["remote"],
                local_or_remote="remote",
                privacy_classification="remote",
            ),
            # Layout Providers
            ProviderDescriptor(
                provider_id="layout.rtdetr",
                name="RT-DETR Layout Analyzer",
                version="1.0.0",
                capability=Capability.LAYOUT,
                provider_type=ProviderType.LOCAL,
                supported_devices=["cpu", "cuda"],
                privacy_classification="private",
            ),
            ProviderDescriptor(
                provider_id="layout.yolo",
                name="YOLO Layout Analyzer",
                version="8.0.0",
                capability=Capability.LAYOUT,
                provider_type=ProviderType.LOCAL,
                supported_devices=["cpu", "cuda"],
                privacy_classification="private",
            ),
            # Table Providers
            ProviderDescriptor(
                provider_id="table.slanet",
                name="SLANet Table Structure Engine",
                version="1.0.0",
                capability=Capability.TABLE,
                provider_type=ProviderType.LOCAL,
                supported_devices=["cpu", "cuda"],
                privacy_classification="private",
            ),
            # Figure & Formula Providers
            ProviderDescriptor(
                provider_id="figure.local",
                name="Local Figure & Image Analyzer",
                version="1.0.0",
                capability=Capability.FIGURE,
                provider_type=ProviderType.LOCAL,
                privacy_classification="private",
            ),
            ProviderDescriptor(
                provider_id="formula.local",
                name="Local Formula & Math Recognizer",
                version="1.0.0",
                capability=Capability.FORMULA,
                provider_type=ProviderType.LOCAL,
                privacy_classification="private",
            ),
            # VLM Providers
            ProviderDescriptor(
                provider_id="vlm.local",
                name="Local Vision-Language Model Engine",
                version="1.0.0",
                capability=Capability.VLM,
                provider_type=ProviderType.LOCAL,
                supported_devices=["cpu", "cuda"],
                privacy_classification="private",
            ),
            ProviderDescriptor(
                provider_id="vlm.huggingface",
                name="Hugging Face VLM Adapter",
                version="1.0.0",
                capability=Capability.VLM,
                provider_type=ProviderType.HUGGINGFACE_LOCAL,
                privacy_classification="private",
            ),
            ProviderDescriptor(
                provider_id="vlm.remote",
                name="Generic Remote VLM Service",
                version="1.0.0",
                capability=Capability.VLM,
                provider_type=ProviderType.REMOTE_API,
                local_or_remote="remote",
                privacy_classification="remote",
            ),
            ProviderDescriptor(
                provider_id="vlm.openai",
                name="OpenAI-compatible VLM Endpoint",
                version="1.0.0",
                capability=Capability.VLM,
                provider_type=ProviderType.OPENAI_COMPATIBLE,
                local_or_remote="remote",
                privacy_classification="remote",
            ),
        ]
        for desc in builtins:
            self.register_descriptor(desc)

    def register_descriptor(self, descriptor: ProviderDescriptor) -> None:
        """Register a provider descriptor."""
        pid = descriptor.provider_id.lower()
        if pid in self._descriptors:
            logger.info("Updating descriptor for registered provider '%s'", pid)
        self._descriptors[pid] = descriptor

    def unregister(self, provider_id: str) -> Optional[ProviderDescriptor]:
        """Unregister a provider by ID."""
        pid = provider_id.lower()
        self._instances.pop(pid, None)
        return self._descriptors.pop(pid, None)

    def get_descriptor(self, provider_id: str) -> ProviderDescriptor:
        """Get provider descriptor by ID."""
        pid = provider_id.lower()
        if pid not in self._descriptors:
            raise ProviderNotFoundError(f"Provider '{provider_id}' is not registered in ProviderRegistry.")
        return self._descriptors[pid]

    def list_descriptors(
        self,
        capability: Optional[Capability] = None,
        privacy_policy: Optional[PrivacyPolicy] = None,
    ) -> List[ProviderDescriptor]:
        """
        List descriptors filtered by capability and privacy policy constraints.
        """
        descs = list(self._descriptors.values())
        if capability is not None:
            descs = [d for d in descs if d.capability == capability]

        if privacy_policy is not None:
            if privacy_policy == PrivacyPolicy.LOCAL_ONLY:
                descs = [d for d in descs if d.local_or_remote == "local"]
            elif privacy_policy == PrivacyPolicy.REMOTE_ONLY:
                descs = [d for d in descs if d.local_or_remote == "remote"]

        return descs

    def get_health(self, provider_id: str) -> ProviderHealth:
        """Check provider health status via ProviderValidator."""
        desc = self.get_descriptor(provider_id)
        return ProviderValidator.validate_provider(desc)


# Global Singleton
default_provider_registry = ProviderRegistry()
