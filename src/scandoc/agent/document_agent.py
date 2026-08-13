"""
Central DocumentAgent orchestrating inspection, planning, execution, validation, and decision tracing.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple, Union

from scandoc.agent.executor import AgentExecutionEngine
from scandoc.agent.inspector import AgentDocumentInspector, DocumentCharacteristics
from scandoc.agent.models import AgentConfig, DecisionTrace, PagePlan, ProcessingPlan
from scandoc.agent.planner import BasePlanningModel, DeterministicPlanner
from scandoc.agent.taxonomy import AgentState, PrivacyPolicy
from scandoc.models import DocumentIR

logger = logging.getLogger("scandoc.agent.document_agent")


class DocumentAgent:
    """
    Agentic Document Routing and Orchestration control plane.
    Inspects documents, builds page plans, selects providers, executes stages concurrently,
    validates outputs, and produces explainable decision traces.
    """

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        planner: Optional[BasePlanningModel] = None,
    ):
        self._config = config or AgentConfig()
        self._planner = planner or DeterministicPlanner()
        self._executor = AgentExecutionEngine(self._config)
        self._state = AgentState.INSPECTING
        self._traces: List[DecisionTrace] = []

    @property
    def config(self) -> AgentConfig:
        return self._config

    @property
    def state(self) -> AgentState:
        return self._state

    @property
    def traces(self) -> List[DecisionTrace]:
        return list(self._traces)

    def cancel(self) -> None:
        """Cancel ongoing agent execution."""
        self._state = AgentState.CANCELLED
        self._executor.cancel()

    def inspect(self, source: Union[str, Path, bytes]) -> DocumentCharacteristics:
        """Inspect document source and return structural characteristics."""
        self._state = AgentState.INSPECTING
        return AgentDocumentInspector.inspect_document(source)

    def plan(self, source: Union[str, Path, bytes]) -> ProcessingPlan:
        """Inspect document and construct processing plan."""
        doc_chars = self.inspect(source)
        self._state = AgentState.PLANNING
        plan = self._planner.create_plan(doc_chars, self._config)
        
        # Log decision trace for fast path vs OCR
        for p_plan in plan.page_plans:
            caps_str = ", ".join(c.value for c in p_plan.capabilities)
            self._traces.append(
                DecisionTrace(
                    page_index=p_plan.page_index,
                    decision="plan_capabilities",
                    reason=f"Assigned capabilities [{caps_str}] based on native text ratio",
                    provider_id=next(iter(p_plan.providers.values()), "default"),
                    mode="LOCAL",
                )
            )

        return plan

    def process(self, source: Union[str, Path, bytes]) -> Tuple[DocumentIR, List[DecisionTrace]]:
        """
        Full agentic orchestration pipeline: Inspect -> Plan -> Execute -> Validate -> Finalize.
        """
        plan = self.plan(source)
        self._state = AgentState.EXECUTING

        try:
            doc_ir, final_traces = self._executor.execute_plan(plan, source, self._traces)
            self._state = AgentState.COMPLETED
            return doc_ir, final_traces
        except Exception as e:
            self._state = AgentState.FAILED
            logger.error("Agent execution failed: %s", e)
            raise

    def explain_decision(self, page_index: int) -> List[DecisionTrace]:
        """Return explainability decision traces for a specific page."""
        return [t for t in self._traces if t.page_index == page_index]
