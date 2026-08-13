"""
Exception classes for VLM Provider System and Local Vision-Language Runtime.
"""


class VlmError(Exception):
    """Base exception for all VLM errors."""
    pass


class VlmProviderUnavailableError(VlmError):
    """Raised when a requested VLM provider is not installed or model is missing."""
    pass


class PrivacyViolationError(VlmError):
    """Raised when a remote VLM provider is invoked without explicit user authorization."""
    pass


class VlmInferenceError(VlmError):
    """Raised when VLM inference fails or encounters a runtime error."""
    pass


class VlmOutputValidationError(VlmError):
    """Raised when VLM output fails schema or JSON validation."""
    pass
