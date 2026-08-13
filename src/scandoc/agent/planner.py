"""
Deterministic page-level planner constructing ProcessingPlans and dependency graphs.
"""

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, List, Optional
import uuid

from scandoc.agent.exceptions import PolicyViolationError
from scandoc.agent.inspector import DocumentCharacteristics
from scandoc.agent.models import AgentConfig, PagePlan, ProcessingPlan
from scandoc.agent.taxonomy import Capability, PrivacyPolicy

logger = logging.getLogger("scandoc.agent.planner")


class BasePlanningModel(ABC):
    """
    Abstract interface for document planning models (Deterministic, LLM-based).
    """

    @abstractmethod
    def create_plan(
        self,
        doc_chars: DocumentCharacteristics,
        config: Optional[AgentConfig] = None,
    ) -> ProcessingPlan:
        """Construct ProcessingPlan from DocumentCharacteristics."""
        pass


class DeterministicPlanner(BasePlanningModel):
    """
    Rule-based deterministic planner creating page-level processing plans.
    Implements fast-path native extraction, selective OCR routing, and capability dependencies.
    Does NOT require an LLM.
    """

    def create_plan(
        self,
        doc_chars: DocumentCharacteristics,
        config: Optional[AgentConfig] = None,
    ) -> ProcessingPlan:
        cfg = config or AgentConfig()
        doc_id = f"doc_plan_{uuid.uuid4().hex[:8]}"

        page_plans: List[PagePlan] = []
        for p_chars in doc_chars.pages:
            p_plan = self._plan_page(p_chars, doc_chars.format_name, cfg)
            page_plans.append(p_plan)

        exec_mode = "local" if cfg.privacy_policy in (PrivacyPolicy.LOCAL_ONLY, PrivacyPolicy.LOCAL_PREFERRED) else "remote"

        return ProcessingPlan(
            document_id=doc_id,
            page_plans=page_plans,
            execution_mode=exec_mode,
            privacy_classification="private",
        )

    def _plan_page(self, p_chars: Any, format_name: str, cfg: AgentConfig) -> PagePlan:
        caps: List[Capability] = []
        provs: Dict[Capability, str] = {}
        models: Dict[Capability, str] = {}

        # 1. Fast-Path Native Extraction vs OCR
        if format_name == "pdf" and p_chars.native_text_ratio >= 0.8 and p_chars.scan_probability < 0.2:
            # Native Fast Path
            caps.append(Capability.NATIVE_PDF)
            provs[Capability.NATIVE_PDF] = "native_pdf_backend"
            models[Capability.NATIVE_PDF] = "pdfminer_engine"
        else:
            # OCR Routing
            caps.append(Capability.OCR)
            provs[Capability.OCR] = "rapidocr"
            models[Capability.OCR] = "rapidocr_onnx"

        # 2. Layout Routing
        if p_chars.scan_probability >= 0.5 or p_chars.image_density > 0.3 or p_chars.has_tables:
            caps.append(Capability.LAYOUT)
            provs[Capability.LAYOUT] = "rtdetr_layout"
            models[Capability.LAYOUT] = "rtdetr_doclaynet"

        # 3. Table Routing
        if p_chars.has_tables:
            caps.append(Capability.TABLE)
            provs[Capability.TABLE] = "slanet_table"
            models[Capability.TABLE] = "slanet_v1"

        # 4. Figure Routing
        if p_chars.has_figures:
            caps.append(Capability.FIGURE)
            provs[Capability.FIGURE] = "local_figure_analyzer"
            models[Capability.FIGURE] = "basic_figure_v1"

        # 5. Formula Routing
        if getattr(p_chars, "has_formulas", False):
            caps.append(Capability.FORMULA)
            provs[Capability.FORMULA] = "local_formula_recognizer"
            models[Capability.FORMULA] = "texify_v1"

        return PagePlan(
            page_index=p_chars.page_index,
            capabilities=caps,
            providers=provs,
            models=models,
            estimated_cost=0.0,
            estimated_latency_ms=15.0 * len(caps),
        )
