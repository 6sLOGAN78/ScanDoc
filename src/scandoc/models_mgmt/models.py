"""
Pydantic data models for ModelSpec, ValidationResult, and configuration.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from scandoc.models_mgmt.taxonomy import (
    ModelFormat,
    ModelSource,
    ModelState,
    QuantizationType,
    TaskType,
)


class ModelSpec(BaseModel):
    """
    Provider-independent specification describing a managed machine learning model artifact.
    """
    model_id: str = Field(..., description="Unique model identifier (e.g. 'org/model-name' or 'slanet_v1')")
    provider: str = Field("scandoc", description="Provider ID responsible for model inference")
    model_name: str = Field(..., description="Human-readable model name")
    version: str = Field("1.0.0", description="Model semantic version")
    revision: str = Field("main", description="Git branch or commit revision hash")
    architecture: str = Field("unknown", description="Neural architecture (e.g. 'RT-DETR', 'SLANet', 'Transformer')")
    task: TaskType = Field(TaskType.OTHER, description="Task category (OCR, LAYOUT, TABLE, etc.)")
    format: ModelFormat = Field(ModelFormat.ONNX, description="Weights format (ONNX, PyTorch, SafeTensors)")
    source: ModelSource = Field(ModelSource.LOCAL_PATH, description="Source origin (LOCAL_PATH, HUGGINGFACE, URL)")
    url: Optional[str] = Field(None, description="Download URL or HF repo string")
    filename: Optional[str] = Field(None, description="Target model weights filename (e.g. 'model.onnx')")
    size_bytes: int = Field(0, ge=0, description="Artifact size in bytes")
    checksum_sha256: Optional[str] = Field(None, description="SHA-256 verification hash")
    license: Optional[str] = Field(None, description="Model open-source license string")
    supported_runtimes: List[str] = Field(default_factory=list, description="Supported execution runtimes ('onnxruntime', 'torch')")
    supported_devices: List[str] = Field(default_factory=list, description="Supported hardware devices ('cpu', 'cuda', 'openvino')")
    quantization: QuantizationType = Field(QuantizationType.FP32, description="Quantization precision (FP32, FP16, INT8, INT4)")
    precision: str = Field("fp32", description="Precision string")
    local_path: Optional[str] = Field(None, description="Local filesystem path to installed model weights")
    state: ModelState = Field(ModelState.UNKNOWN, description="Current lifecycle state")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Custom model metadata key-values")


class ValidationResult(BaseModel):
    """
    Structured outcome of model integrity, checksum, and hardware compatibility validation.
    """
    is_valid: bool = Field(..., description="True if model passes all validation checks")
    errors: List[str] = Field(default_factory=list, description="Validation error messages if invalid")
    checksum_verified: bool = Field(False, description="True if SHA-256 checksum matched expected value")
    hardware_compatible: bool = Field(True, description="True if target hardware runtime supports model")
