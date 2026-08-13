"""
Taxonomy enums for model tasks, sources, formats, states, and quantization types.
"""

from enum import Enum


class TaskType(str, Enum):
    """Document intelligence model task categories."""
    OCR = "ocr"
    LAYOUT = "layout"
    TABLE = "table"
    FIGURE = "figure"
    FORMULA = "formula"
    VLM = "vlm"
    EMBEDDING = "embedding"
    OTHER = "other"


class ModelSource(str, Enum):
    """Source origin of model artifacts."""
    LOCAL_PATH = "local_path"
    HUGGINGFACE = "huggingface"
    URL = "url"
    BUNDLED = "bundled"
    USER_PROVIDED = "user_provided"


class ModelFormat(str, Enum):
    """Model weights storage and execution format."""
    ONNX = "onnx"
    PYTORCH = "pytorch"
    SAFETENSORS = "safetensors"
    GGUF = "gguf"
    OPENVINO = "openvino"
    TENSORRT = "tensorrt"
    OTHER = "other"


class ModelState(str, Enum):
    """Lifecycle states of managed models."""
    UNKNOWN = "unknown"
    DISCOVERED = "discovered"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    VERIFYING = "verifying"
    READY = "ready"
    LOADING = "loading"
    LOADED = "loaded"
    UNLOADING = "unloading"
    FAILED = "failed"
    CORRUPTED = "corrupted"


class QuantizationType(str, Enum):
    """Model weight quantization precision."""
    FP32 = "fp32"
    FP16 = "fp16"
    BF16 = "bf16"
    INT8 = "int8"
    INT4 = "int4"
    OTHER = "other"
