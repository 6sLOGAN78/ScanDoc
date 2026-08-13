"""
Exception classes for Agentic Document Routing and Orchestration subsystem.
"""


class AgentError(Exception):
    """Base exception for all document agent orchestration errors."""
    pass


class PlanningError(AgentError):
    """Raised when document page-level planning or dependency resolution fails."""
    pass


class PolicyViolationError(AgentError):
    """Raised when execution violates privacy policy (e.g., LOCAL_ONLY)."""
    pass


class AgentExecutionError(AgentError):
    """Raised when pipeline execution engine fails."""
    pass


class AgentCancelledError(AgentError):
    """Raised when document agent processing is explicitly cancelled."""
    pass
