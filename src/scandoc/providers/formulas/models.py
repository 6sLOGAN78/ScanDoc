"""
Data models for formula configuration, representation, and FormulaResult.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from scandoc.models.geometry import BoundingBox, Point2D
from scandoc.models.provenance import Provenance
from scandoc.providers.ocr.secrets import SecretRef
from scandoc.providers.formulas.taxonomy import FormulaType, MathFormat, ProviderType


class FormulaConfig(BaseModel):
    """
    Configuration model for formula and mathematical content providers.
    """
    model_name: str = Field("BasicFormulaRecognizer", description="Target formula model identifier")
    provider_type: ProviderType = Field(ProviderType.LOCAL, description="Provider execution type (LOCAL, HUGGINGFACE, REMOTE)")
    model_path: Optional[str] = Field(None, description="Path to local ONNX/Torch model weights")
    endpoint: Optional[str] = Field(None, description="HTTP endpoint for remote providers")
    api_key_ref: Optional[SecretRef] = Field(None, description="Secure reference to API key")
    device: str = Field("auto", description="Execution device ('cpu', 'cuda', 'auto')")
    allow_remote: bool = Field(False, description="Privacy flag: Must be True to invoke remote providers")
    extra_options: Dict[str, str] = Field(default_factory=dict, description="Provider-specific options")


class FormulaRepresentation(BaseModel):
    """
    Mathematical syntax representation (LaTeX, MathML, Plaintext).
    """
    format: MathFormat = Field(MathFormat.LATEX, description="Representation format type")
    value: str = Field("", description="Mathematical expression string value")


class FormulaResult(BaseModel):
    """
    Structured outcome of mathematical content detection and recognition.
    """
    formula_id: str = Field(..., description="Unique formula identifier")
    page_index: int = Field(0, ge=0, description="0-indexed document page index")
    bbox: BoundingBox = Field(..., description="Normalized bounding box [left, top, right, bottom]")
    polygon: Optional[List[Point2D]] = Field(None, description="Optional contour polygon points")
    formula_type: FormulaType = Field(FormulaType.DISPLAY, description="Formula type (inline, display, numbered, multi_line)")
    representation: FormulaRepresentation = Field(..., description="Recognized mathematical syntax representation")
    equation_number: Optional[str] = Field(None, description="Optional equation number tag (e.g. '(1)', '(3.2)')")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Formula recognition confidence score")
    provider_id: str = Field(..., description="Provider ID (e.g. 'local_formula_recognizer')")
    model_id: str = Field(..., description="Model ID (e.g. 'BasicFormulaRecognizer-v1')")
    processing_time_ms: float = Field(0.0, ge=0.0, description="Inference latency in ms")
    provenance: Optional[Provenance] = Field(None, description="Provenance metadata")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Metadata (e.g. symbol_count, contains_matrix)")

    @field_validator("confidence")
    @classmethod
    def validate_confidence_bounds(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError(f"Formula confidence ({v}) must be between 0.0 and 1.0")
        return round(v, 4)
