"""
Unit and integration test suite for Phase 13: Formula & Mathematical Content.
"""

import pytest

from scandoc.models.blocks import FormulaBlock, FormulaFormat
from scandoc.models.geometry import BoundingBox
from scandoc.models.provenance import ProcessingStage, Provenance
from scandoc.providers.formulas import (
    BaseFormulaProvider,
    FormulaConfig,
    FormulaProviderRegistry,
    FormulaRepresentation,
    FormulaResult,
    FormulaType,
    GenericRemoteFormulaProvider,
    HuggingFaceFormulaAdapter,
    LocalFormulaProvider,
    MathFormat,
    ProviderType,
    formula_result_to_document_ir,
    PrivacyViolationError,
)


def test_formula_result_and_representation_schema():
    """Test FormulaResult and FormulaRepresentation schemas."""
    rep = FormulaRepresentation(format=MathFormat.LATEX, value=r"\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}")
    res = FormulaResult(
        formula_id="f1",
        page_index=0,
        bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.3, is_normalized=True),
        formula_type=FormulaType.DISPLAY,
        representation=rep,
        equation_number="(3.14)",
        provider_id="local_test",
        model_id="test_m",
    )

    assert res.representation.format == MathFormat.LATEX
    assert res.equation_number == "(3.14)"
    assert res.formula_type == FormulaType.DISPLAY


def test_local_formula_provider():
    """Test LocalFormulaProvider formula recognition and equation number extraction."""
    prov = LocalFormulaProvider()
    res = prov.recognize_formula(r"E = mc^2 (1)", formula_type=FormulaType.NUMBERED)

    assert res.formula_type == FormulaType.NUMBERED
    assert res.equation_number == "(1)"
    assert res.representation.value == r"E = mc^2 (1)"
    assert res.provenance.provider == "local_formula_recognizer"


def test_privacy_remote_formula_provider_enforcement():
    """Security Test: Remote formula providers MUST raise PrivacyViolationError if allow_remote=False."""
    remote_p = GenericRemoteFormulaProvider(
        config=FormulaConfig(
            endpoint="https://api.math-ocr.internal/v1/latex",
            allow_remote=False,
        )
    )

    with pytest.raises(PrivacyViolationError):
        remote_p.initialize()

    with pytest.raises(PrivacyViolationError):
        remote_p.recognize_formula(r"\alpha + \beta")


def test_formula_provider_registry():
    """Test FormulaProviderRegistry registration, selection, and privacy filtering."""
    registry = FormulaProviderRegistry(register_defaults=True)
    assert len(registry.list_providers()) == 3

    # Default selection returns local provider
    local_p = registry.select_provider(FormulaConfig(allow_remote=False))
    assert local_p.provider_type == ProviderType.LOCAL


def test_formula_result_to_document_ir_conversion():
    """Test converting FormulaResult into DocumentIR FormulaBlock model."""
    rep = FormulaRepresentation(format=MathFormat.LATEX, value=r"\frac{a+b}{c-d}")
    f_res = FormulaResult(
        formula_id="f_ir_1",
        page_index=0,
        bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.3, is_normalized=True),
        formula_type=FormulaType.DISPLAY,
        representation=rep,
        provider_id="local_formula_recognizer",
        model_id="BasicFormulaRecognizer-v1",
    )

    f_block: FormulaBlock = formula_result_to_document_ir(f_res)
    assert isinstance(f_block, FormulaBlock)
    assert f_block.id == "f_ir_1"
    assert f_block.expression == r"\frac{a+b}{c-d}"
    assert f_block.format == FormulaFormat.LATEX
    assert f_block.provenance.provider == "local_formula_recognizer"
