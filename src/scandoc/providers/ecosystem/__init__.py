"""
Multi-Provider Ecosystem & User-Configurable Providers for scanDOC.
"""

from scandoc.providers.ecosystem.credentials import CredentialReference
from scandoc.providers.ecosystem.exceptions import (
    EcosystemError,
    ProviderConfigurationError,
    ProviderNotFoundError,
    ProviderValidationError,
    ProviderVersionMismatchError,
)
from scandoc.providers.ecosystem.factory import ProviderFactory
from scandoc.providers.ecosystem.fallback import ProviderFallbackEngine
from scandoc.providers.ecosystem.models import (
    FallbackTrace,
    ProviderDescriptor,
    ProviderHealth,
    UserProviderConfig,
)
from scandoc.providers.ecosystem.registry import ProviderRegistry, default_provider_registry
from scandoc.providers.ecosystem.taxonomy import (
    ProviderHealthState,
    ProviderLifecycleState,
    ProviderType,
)
from scandoc.providers.ecosystem.validator import ProviderValidator

__all__ = [
    "ProviderRegistry",
    "default_provider_registry",
    "ProviderDescriptor",
    "ProviderHealth",
    "UserProviderConfig",
    "FallbackTrace",
    "CredentialReference",
    "ProviderFactory",
    "ProviderValidator",
    "ProviderFallbackEngine",
    "ProviderType",
    "ProviderHealthState",
    "ProviderLifecycleState",
    "EcosystemError",
    "ProviderNotFoundError",
    "ProviderConfigurationError",
    "ProviderValidationError",
    "ProviderVersionMismatchError",
]
