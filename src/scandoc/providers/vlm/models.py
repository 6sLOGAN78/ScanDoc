"""
Data models for VLM configuration, VlmRequest payload, and VlmResult.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from scandoc.models.geometry import BoundingBox, Point2D
from scandoc.models.provenance import Provenance
from scandoc.providers.ocr.secrets import SecretRef
from scandoc.providers.vlm.taxonomy import ProviderType, VlmExecutionMode, VlmTaskType


class VlmConfig(BaseModel):
    """
    Configuration model for Vision-Language Model providers.
    """
    model_name: str = Field("Qwen2-VL-7B-Instruct", description="Target VLM identifier")
    provider_type: ProviderType = Field(ProviderType.LOCAL, description="Provider type (LOCAL, HUGGINGFACE, REMOTE)")
    model_path: Optional[str] = Field(None, description="Path to local VLM weights directory")
    endpoint: Optional[str] = Field(None, description="Remote API endpoint URL")
    api_key_ref: Optional[SecretRef] = Field(None, description="Secure reference to API key")
    device: str = Field("auto", description="Execution device ('cpu', 'cuda', 'auto')")
    allow_remote: bool = Field(False, description="Privacy flag: Must be True to invoke remote VLM APIs")
    max_tokens: int = Field(1024, ge=1, description="Maximum token generation limit")
    temperature: float = Field(0.0, ge=0.0, le=2.0, description="Sampling temperature")
    extra_options: Dict[str, str] = Field(default_factory=dict, description="Provider-specific options")


class VlmRequest(BaseModel):
    """
    Provider-independent request payload for VLM visual reasoning.
    """
    task: VlmTaskType = Field(VlmTaskType.PAGE_UNDERSTANDING, description="VLM task type category")
    prompt: str = Field(..., description="Prompt or instruction for VLM visual reasoning")
    image_bytes: Optional[bytes] = Field(None, description="Optional raw image bytes payload")
    image_path: Optional[str] = Field(None, description="Optional path to page or region image file")
    page_index: int = Field(0, ge=0, description="0-indexed document page number")
    bbox: Optional[BoundingBox] = Field(None, description="Optional bounding box of cropped image region")
    text_context: Optional[str] = Field(None, description="Optional OCR or native PDF text context")
    output_format: str = Field("json", description="Expected output format ('json' or 'text')")
    provenance: Optional[Provenance] = Field(None, description="Provenance metadata for request")


class VlmResult(BaseModel):
    """
    Structured outcome of VLM visual reasoning and structured extraction.
    """
    task: VlmTaskType = Field(..., description="Executed VLM task category")
    text_result: Optional[str] = Field(None, description="Raw textual output from VLM")
    structured_result: Optional[Dict[str, Any]] = Field(None, description="Validated JSON structured output")
    confidence: Optional[float] = Field(None, description="Optional confidence score (None if not provided by model)")
    provider_id: str = Field(..., description="VLM Provider ID")
    model_id: str = Field(..., description="VLM Model ID")
    execution_mode: VlmExecutionMode = Field(VlmExecutionMode.LOCAL, description="Execution mode (LOCAL or REMOTE)")
    device: str = Field("cpu", description="Execution device identifier")
    processing_time_ms: float = Field(0.0, ge=0.0, description="Inference latency in ms")
    provenance: Optional[Provenance] = Field(None, description="Provenance metadata")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Custom execution metadata")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v < 0.0 or v > 1.0:
                raise ValueError(f"VLM confidence ({v}) must be between 0.0 and 1.0")
            return round(v, 4)
        return None
