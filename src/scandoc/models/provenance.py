"""
Provenance tracking primitives for scanDOC DocumentIR.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ProcessingStage(str, Enum):
    """Document processing pipeline stage."""
    INSPECTION = "INSPECTION"
    NATIVE_EXTRACTION = "NATIVE_EXTRACTION"
    LAYOUT_ANALYSIS = "LAYOUT_ANALYSIS"
    OCR = "OCR"
    TABLE_RECOGNITION = "TABLE_RECOGNITION"
    FORMULA_RECOGNITION = "FORMULA_RECOGNITION"
    VLM = "VLM"
    POST_PROCESSING = "POST_PROCESSING"
    MANUAL = "MANUAL"


class Provenance(BaseModel):
    """
    Detailed provenance metadata tracing the origin, provider, model, and confidence
    of extracted document elements.
    """
    provider: str = Field(
        ...,
        description="Name of extraction provider or engine (e.g., 'pypdfium2', 'rapidocr', 'rt-detr')"
    )
    model: Optional[str] = Field(
        None,
        description="Specific model identifier or checkpoint version if ML model was used"
    )
    confidence: Optional[float] = Field(
        None,
        description="Confidence score assigned by the provider (0.0 to 1.0)"
    )
    stage: Optional[ProcessingStage] = Field(
        None,
        description="Processing pipeline stage during which element was generated"
    )
    source_ref: Optional[str] = Field(
        None,
        description="Pointer or reference to raw source stream or object ID"
    )
    version: Optional[str] = Field(
        None,
        description="Engine or provider library version"
    )
    timestamp: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp string when processing occurred"
    )

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: Optional[float]) -> Optional[float]:
        """Validate confidence score bounds."""
        if v is not None:
            if v < 0.0 or v > 1.0:
                raise ValueError(f"Confidence score ({v}) must be between 0.0 and 1.0")
        return v
