"""
Parallel Page Execution Engine dispatching capability stages and constructing DocumentIR.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from typing import Any, Dict, List, Optional, Tuple
import uuid

from scandoc.agent.exceptions import AgentCancelledError, AgentExecutionError
from scandoc.agent.models import AgentConfig, DecisionTrace, PagePlan, ProcessingPlan
from scandoc.agent.taxonomy import Capability
from scandoc.agent.validator import AgentPlanValidator
from scandoc.models import DocumentIR, DocumentMetadata, Page
from scandoc.models.blocks import ParagraphBlock, TextBlock
from scandoc.models.geometry import BoundingBox
from scandoc.models.provenance import ProcessingStage, Provenance
from scandoc.providers.ocr.models import OCRResult, OCRTextRegion

logger = logging.getLogger("scandoc.agent.executor")


class AgentExecutionEngine:
    """
    Executes ProcessingPlans concurrently across pages, respects cancellation,
    handles partial page failures, and constructs final DocumentIR.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        self._config = config or AgentConfig()
        self._is_cancelled = False

    def cancel(self) -> None:
        """Cancel ongoing execution."""
        self._is_cancelled = True

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    def execute_plan(
        self,
        plan: ProcessingPlan,
        source_data: Any,
        traces: Optional[List[DecisionTrace]] = None,
    ) -> Tuple[DocumentIR, List[DecisionTrace]]:
        """
        Execute document processing plan across pages.
        """
        if self._is_cancelled:
            raise AgentCancelledError("Execution cancelled before starting.")

        active_traces = traces if traces is not None else []
        ir_pages: List[Page] = []

        # Execute page plans concurrently using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self._config.max_concurrency) as executor:
            future_to_plan = {
                executor.submit(self._execute_page, p_plan, source_data, active_traces): p_plan
                for p_plan in plan.page_plans
            }

            for future in as_completed(future_to_plan):
                if self._is_cancelled:
                    raise AgentCancelledError("Execution cancelled during page processing.")
                p_plan = future_to_plan[future]
                try:
                    page_ir = future.result()
                    ir_pages.append(page_ir)
                except Exception as e:
                    logger.error("Partial failure on page %d: %s", p_plan.page_index, e)
                    # Failure isolation: append empty page fallback
                    ir_pages.append(Page(page_number=p_plan.page_index + 1, blocks=[]))

        # Sort pages into original page sequence
        ir_pages.sort(key=lambda p: p.page_index)

        doc_ir = DocumentIR(
            metadata=DocumentMetadata(
                id=plan.document_id,
                name=f"Document_{plan.document_id}",
                page_count=len(ir_pages),
            ),
            pages=ir_pages,
        )

        return doc_ir, active_traces

    def _execute_page(
        self,
        p_plan: PagePlan,
        source_data: Any,
        traces: List[DecisionTrace],
    ) -> Page:
        stage_outputs: Dict[Capability, Any] = {}
        blocks: List[Any] = []

        for cap in p_plan.capabilities:
            if self._is_cancelled:
                raise AgentCancelledError(f"Cancelled during capability '{cap.value}'.")

            prov_id = p_plan.providers.get(cap, "default_provider")
            model_id = p_plan.models.get(cap, "default_model")

            # Record trace
            traces.append(
                DecisionTrace(
                    page_index=p_plan.page_index,
                    decision=f"execute_{cap.value}",
                    reason=f"Processing plan capability '{cap.value}'",
                    provider_id=prov_id,
                    mode="LOCAL",
                )
            )

            # Stage execution simulation & IR block mapping
            if cap == Capability.NATIVE_PDF:
                b = ParagraphBlock(
                    id=f"p_{p_plan.page_index}_0",
                    text="Native PDF text content extracted from content stream.",
                    bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.3, is_normalized=True),
                    provenance=Provenance(provider=prov_id, model=model_id, stage=ProcessingStage.NATIVE_EXTRACTION),
                )
                blocks.append(b)
                stage_outputs[cap] = b

            elif cap == Capability.OCR:
                ocr_res = OCRResult(
                    full_text="OCR text content recognized from document image.",
                    regions=[
                        OCRTextRegion(
                            text="OCR text region",
                            bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.3, is_normalized=True),
                            confidence=0.98,
                        )
                    ],
                    provider_id=prov_id,
                    model_id=model_id,
                    image_width=612,
                    image_height=792,
                )
                b = ParagraphBlock(
                    id=f"p_{p_plan.page_index}_ocr",
                    text=ocr_res.full_text,
                    bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.3, is_normalized=True),
                    provenance=Provenance(provider=prov_id, model=model_id, stage=ProcessingStage.OCR),
                )
                blocks.append(b)
                stage_outputs[cap] = ocr_res

        # Check validation & VLM escalation if needed
        should_escalate, reason, suggested = AgentPlanValidator.validate_page_results(p_plan, stage_outputs, self._config)
        if should_escalate and suggested == Capability.VLM:
            traces.append(
                DecisionTrace(
                    page_index=p_plan.page_index,
                    decision="escalate_vlm",
                    reason=reason,
                    provider_id="local_vlm_engine",
                    mode="LOCAL",
                )
            )

        return Page(
            page_index=p_plan.page_index,
            width=612.0,
            height=792.0,
            blocks=blocks,
        )
