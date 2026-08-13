"""
Taxonomy enums for provider types, health states, and lifecycle states.
"""

from enum import Enum


class ProviderType(str, Enum):
    """
    Categorization of provider execution and hosting models.
    """
    LOCAL = "local"
    HUGGINGFACE_LOCAL = "huggingface_local"
    HUGGINGFACE_REMOTE = "huggingface_remote"
    REMOTE_API = "remote_api"
    OPENAI_COMPATIBLE = "openai_compatible"
    CUSTOM = "custom"


class ProviderHealthState(str, Enum):
    """
    Structured health state classification for providers.
    """
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    MISCONFIGURED = "misconfigured"
    MODEL_MISSING = "model_missing"
    RUNTIME_UNAVAILABLE = "runtime_unavailable"
    AUTHENTICATION_REQUIRED = "authentication_required"
    REMOTE_UNREACHABLE = "remote_unreachable"
    UNKNOWN = "unknown"


class ProviderLifecycleState(str, Enum):
    """
    Explicit lifecycle states for provider instances.
    """
    DISCOVERED = "discovered"
    CONFIGURED = "configured"
    VALIDATING = "validating"
    READY = "ready"
    RUNNING = "running"
    DEGRADED = "degraded"
    FAILED = "failed"
    DISABLED = "disabled"
