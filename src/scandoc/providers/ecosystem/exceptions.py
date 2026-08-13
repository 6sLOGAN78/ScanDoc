"""
Exception classes for Multi-Provider Ecosystem subsystem.
"""


class EcosystemError(Exception):
    """Base exception for all provider ecosystem errors."""
    pass


class ProviderNotFoundError(EcosystemError):
    """Raised when a requested provider ID is not registered."""
    pass


class ProviderConfigurationError(EcosystemError):
    """Raised when provider configuration is invalid or missing required parameters."""
    pass


class ProviderValidationError(EcosystemError):
    """Raised when provider health check or validation fails."""
    pass


class ProviderVersionMismatchError(EcosystemError):
    """Raised when a provider API version is incompatible with core scanDOC."""
    pass
