"""
Taxonomy enums and exit code definitions for scanDOC CLI.
"""

from enum import IntEnum, Enum


class ExitCode(IntEnum):
    """Standardized scanDOC CLI exit codes."""
    SUCCESS = 0
    INVALID_ARGUMENTS = 1
    INPUT_ERROR = 2
    PROCESSING_ERROR = 3
    CONFIGURATION_ERROR = 4
    PROVIDER_MODEL_ERROR = 5
    SIGINT_CANCELLED = 6
    UNEXPECTED_ERROR = 99


class BatchErrorPolicy(str, Enum):
    """Batch directory execution error policies."""
    CONTINUE_ON_ERROR = "continue-on-error"
    FAIL_FAST = "fail-fast"
