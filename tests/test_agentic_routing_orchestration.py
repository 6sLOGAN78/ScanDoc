"""
Unit and integration test suite for Phase 16 & Phase 35: Agentic Document Routing & Orchestration.
"""

import tempfile
import pytest

from scandoc.agent import (
    AdaptiveRoutingEngine,
    AgentCancelledError,
    AgentConfig,
    AgentDocumentInspector,
    AgentExecutionEngine,
    AgentPlanValidator,
    AgentState,
    Capability,
    ClassificationResult,
    DecisionTrace,
    DeterministicPlanner,
    DocumentAgent,
    DocumentCategoryType,
    DocumentClassifier,
    PagePlan,
    PrivacyPolicy,
    ProcessingPlan,
)
from scandoc.models import DocumentIR
from scandoc.models.geometry import BoundingBox
from scandoc.pipelines import DocumentPipeline, OrderingMode, PipelineConfig
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


# Phase 35 Tests: Dynamic Document Classification & Adaptive Routing Engine

def test_document_classification_categories():
    """Test DocumentClassifier classifying digital PDF, scanned document, forms, and technical reports."""
    res_text = DocumentClassifier.classify(b"Digital PDF text payload content")
    assert isinstance(res_text, ClassificationResult)
    assert res_text.category in (DocumentCategoryType.DIGITAL_PDF, DocumentCategoryType.TECHNICAL_REPORT)
    assert 0.0 <= res_text.overall_complexity <= 1.0
    assert res_text.recommended_routing in ("fast_path", "deep_ml", "vlm_fallback")


def test_adaptive_routing_engine_fast_path():
    """Test AdaptiveRoutingEngine fast-path native extraction for digital text."""
    engine = AdaptiveRoutingEngine()
    doc_ir, traces, telemetry = engine.route_document(b"Digital PDF text content")

    assert isinstance(doc_ir, DocumentIR)
    assert len(traces) >= 1
    assert telemetry["routing_mode"] in ("fast_path", "deep_ml")
    assert telemetry["total_latency_ms"] >= 0.0


def test_document_pipeline_adaptive_mode():
    """Test DocumentPipeline executing with routing_mode='adaptive'."""
    pipe = DocumentPipeline(config=PipelineConfig(routing_mode="adaptive"))
    res = pipe.process(b"Sample text for adaptive pipeline processing.")

    assert res.status == "success"
    assert res.document_ir is not None
    assert res.metrics.documents_processed == 1
