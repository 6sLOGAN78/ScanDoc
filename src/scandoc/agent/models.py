"""
Data models for agent configuration, page plans, processing plans, and decision traces.
"""

import time
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from scandoc.agent.taxonomy import AgentState, Capability, PrivacyPolicy


class AgentConfig(BaseModel):
    """
    Configuration model for DocumentAgent control plane.
    """
    privacy_policy: PrivacyPolicy = Field(PrivacyPolicy.LOCAL_PREFERRED, description="Privacy policy governing provider selection")
    max_retries: int = Field(2, ge=0, description="Maximum escalation/replan retries per page")
    ocr_confidence_threshold: float = Field(0.70, ge=0.0, le=1.0, description="Minimum acceptable OCR confidence before VLM escalation")
    table_threshold: float = Field(0.50, ge=0.0, le=1.0, description="Table region detection likelihood threshold")
    max_concurrency: int = Field(4, ge=1, description="Maximum concurrent page processing threads")
    allow_vlm_escalation: bool = Field(True, description="True if agent is allowed to escalate low-confidence results to VLM")


class PagePlan(BaseModel):
    """
    Page-level processing plan specifying required capabilities and assigned providers.
    """
    page_index: int = Field(..., ge=0, description="0-indexed document page number")
    capabilities: List[Capability] = Field(default_factory=list, description="Ordered required capabilities for page")
    providers: Dict[Capability, str] = Field(default_factory=dict, description="Assigned provider ID per capability")
    models: Dict[Capability, str] = Field(default_factory=dict, description="Assigned model ID per capability")
    estimated_cost: float = Field(0.0, ge=0.0, description="Estimated monetary cost in USD")
    estimated_latency_ms: float = Field(0.0, ge=0.0, description="Estimated execution latency in ms")
    retry_count: int = Field(0, ge=0, description="Current retry attempt count for this page")


class ProcessingPlan(BaseModel):
    """
    Complete document processing plan containing page plans, execution mode, and privacy classification.
    """
    document_id: str = Field(..., description="Unique document identifier")
    page_plans: List[PagePlan] = Field(default_factory=list, description="Ordered list of page plans")
    execution_mode: str = Field("local", description="Execution mode ('local', 'hybrid', 'remote')")
    privacy_classification: str = Field("private", description="Privacy rating ('private', 'confidential', 'public')")
    fallback_options: List[str] = Field(default_factory=list, description="Ordered fallback provider candidates")


class DecisionTrace(BaseModel):
    """
    Structured explainability decision trace entry explaining why a decision was made.
    """
    page_index: int = Field(..., ge=0, description="Target document page index")
    decision: str = Field(..., description="Decision action identifier (e.g. 'run_ocr', 'fast_path_native', 'escalate_vlm')")
    reason: str = Field(..., description="Human-readable justification for the decision")
    provider_id: str = Field(..., description="Selected provider identifier")
    mode: str = Field("LOCAL", description="Execution mode ('LOCAL', 'REMOTE')")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of decision")
