"""
Exception classes for formula and mathematical content subsystem.
"""


class FormulaError(Exception):
    """Base exception for all formula and mathematical content errors."""
    pass


class FormulaProviderUnavailableError(FormulaError):
    """Raised when a requested formula provider or model weights are missing."""
    pass


class PrivacyViolationError(FormulaError):
    """Raised when a remote formula provider is invoked without explicit authorization."""
    pass


class FormulaInferenceError(FormulaError):
    """Raised when formula recognition model execution fails."""
    pass


class InvalidFormulaInputError(FormulaError):
    """Raised when formula input payload is invalid or unreadable."""
    pass
