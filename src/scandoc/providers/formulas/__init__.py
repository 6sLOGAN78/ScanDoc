"""
Formula & Mathematical Content Subsystem for scanDOC.
"""

from scandoc.providers.formulas.base import BaseFormulaProvider
from scandoc.providers.formulas.converter import formula_result_to_document_ir
from scandoc.providers.formulas.exceptions import (
    FormulaError,
    FormulaInferenceError,
    FormulaProviderUnavailableError,
    InvalidFormulaInputError,
    PrivacyViolationError,
)
from scandoc.providers.formulas.huggingface_provider import HuggingFaceFormulaAdapter
from scandoc.providers.formulas.local_provider import LocalFormulaProvider
from scandoc.providers.formulas.models import (
    FormulaConfig,
    FormulaRepresentation,
    FormulaResult,
)
from scandoc.providers.formulas.registry import (
    FormulaProviderRegistry,
    default_formula_registry,
)
from scandoc.providers.formulas.remote_provider import GenericRemoteFormulaProvider
from scandoc.providers.formulas.taxonomy import FormulaType, MathFormat, ProviderType

__all__ = [
    "BaseFormulaProvider",
    "LocalFormulaProvider",
    "HuggingFaceFormulaAdapter",
    "GenericRemoteFormulaProvider",
    "FormulaProviderRegistry",
    "default_formula_registry",
    "FormulaType",
    "MathFormat",
    "ProviderType",
    "FormulaConfig",
    "FormulaRepresentation",
    "FormulaResult",
    "formula_result_to_document_ir",
    "FormulaError",
    "FormulaProviderUnavailableError",
    "PrivacyViolationError",
    "FormulaInferenceError",
    "InvalidFormulaInputError",
]
