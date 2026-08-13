"""
AgentPlanValidator evaluating processing outputs and triggering replanning or VLM escalation.
"""

import logging
from typing import Any, Optional, Tuple

from scandoc.agent.models import AgentConfig, PagePlan
from scandoc.agent.taxonomy import Capability

logger = logging.getLogger("scandoc.agent.validator")


class AgentPlanValidator:
    """
    Validates page processing outcomes against quality criteria, confidence thresholds, and retry limits.
    Triggers replanning or VLM escalation when extraction confidence is insufficient.
    """

    @classmethod
    def validate_page_results(
        cls,
        page_plan: PagePlan,
        stage_outputs: dict[Capability, Any],
        config: AgentConfig,
    ) -> Tuple[bool, str, Optional[Capability]]:
        """
        Validate page outputs and check if replanning or VLM escalation is required.
        
        Returns:
            Tuple[should_escalate, reason, suggested_capability]
        """
        # Check retry limits
        if page_plan.retry_count >= config.max_retries:
            return False, f"Maximum retries ({config.max_retries}) reached for page {page_plan.page_index}.", None

        # Check OCR confidence threshold
        if Capability.OCR in stage_outputs:
            ocr_res = stage_outputs[Capability.OCR]
            conf = getattr(ocr_res, "confidence", None)
            if conf is None and hasattr(ocr_res, "regions") and ocr_res.regions:
                conf = sum(r.confidence for r in ocr_res.regions) / len(ocr_res.regions)
            if conf is None:
                conf = 1.0

            if conf < config.ocr_confidence_threshold:
                if config.allow_vlm_escalation and Capability.VLM not in page_plan.capabilities:
                    return (
                        True,
                        f"Low OCR confidence ({conf:.2f} < {config.ocr_confidence_threshold:.2f}) on page {page_plan.page_index}.",
                        Capability.VLM,
                    )

        return False, "Page processing results passed validation.", None
