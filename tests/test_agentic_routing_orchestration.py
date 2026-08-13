"""
Unit and integration test suite for Phase 16: Agentic Document Routing & Orchestration.
"""

import tempfile
import pytest

from scandoc.agent import (
    AgentCancelledError,
    AgentConfig,
    AgentDocumentInspector,
    AgentExecutionEngine,
    AgentPlanValidator,
    AgentState,
    Capability,
    DecisionTrace,
    DeterministicPlanner,
    DocumentAgent,
    PagePlan,
    PrivacyPolicy,
    ProcessingPlan,
)
from scandoc.models import DocumentIR
from scandoc.models.geometry import BoundingBox
from scandoc.providers.ocr.models import OCRResult, OCRTextRegion


def test_deterministic_planner_fast_path_and_ocr_routing():
    """Test DeterministicPlanner fast-path native extraction vs selective OCR routing."""
    planner = DeterministicPlanner()
    cfg = AgentConfig()

    from scandoc.agent.inspector import DocumentCharacteristics, PageCharacteristics
    from scandoc.pdf.models import DocumentCategory

    # Digital PDF Page
    digital_p = PageCharacteristics(page_index=0, native_text_ratio=0.95, scan_probability=0.05)
    # Scanned PDF Page
    scanned_p = PageCharacteristics(page_index=1, native_text_ratio=0.05, scan_probability=0.95, has_tables=True)

    doc_chars = DocumentCharacteristics(
        format_name="pdf",
        num_pages=2,
        classification=DocumentCategory.HYBRID,
        pages=[digital_p, scanned_p],
    )

    plan = planner.create_plan(doc_chars, cfg)
    assert len(plan.page_plans) == 2

    # Page 0 should use NATIVE_PDF fast path
    p0 = plan.page_plans[0]
    assert Capability.NATIVE_PDF in p0.capabilities
    assert Capability.OCR not in p0.capabilities

    # Page 1 should use OCR + LAYOUT + TABLE
    p1 = plan.page_plans[1]
    assert Capability.OCR in p1.capabilities
    assert Capability.TABLE in p1.capabilities


def test_agent_plan_validator_vlm_escalation():
    """Test AgentPlanValidator escalating low-confidence OCR outputs to VLM."""
    cfg = AgentConfig(ocr_confidence_threshold=0.70, allow_vlm_escalation=True)
    p_plan = PagePlan(page_index=0, capabilities=[Capability.OCR])

    # Low confidence OCR result (0.45 < 0.70)
    low_ocr = OCRResult(
        full_text="Low quality scan",
        regions=[
            OCRTextRegion(
                text="Low quality scan",
                bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.3, is_normalized=True),
                confidence=0.45,
            )
        ],
        provider_id="rapidocr",
        model_id="rapidocr_onnx",
        image_width=100,
        image_height=100,
    )

    should_esc, reason, suggested = AgentPlanValidator.validate_page_results(
        p_plan, {Capability.OCR: low_ocr}, cfg
    )

    assert should_esc is True
    assert suggested == Capability.VLM
    assert "Low OCR confidence" in reason


def test_document_agent_execution_and_explainability_traces():
    """Test DocumentAgent end-to-end processing, execution, and decision tracing."""
    agent = DocumentAgent(config=AgentConfig(privacy_policy=PrivacyPolicy.LOCAL_PREFERRED))

    # Process bytes input
    doc_ir, traces = agent.process(b"Simple text content for agent testing")

    assert isinstance(doc_ir, DocumentIR)
    assert agent.state == AgentState.COMPLETED
    assert len(traces) >= 1

    # Explain decision for page 0
    p0_traces = agent.explain_decision(0)
    assert len(p0_traces) >= 1
    assert p0_traces[0].page_index == 0


def test_agent_cancellation():
    """Test explicit cancellation of ongoing DocumentAgent execution."""
    agent = DocumentAgent()
    agent.cancel()

    with pytest.raises(AgentCancelledError):
        agent.process(b"Sample payload for cancellation test")
