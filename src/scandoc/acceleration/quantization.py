"""
Model Quantization Engine providing FP16 and INT8 ONNX graph optimization and precision management.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from scandoc.acceleration.models import PrecisionMode

logger = logging.getLogger("scandoc.acceleration.quantization")


class QuantizationConfig(BaseModel):
    """Configuration for model weight quantization."""
    precision: PrecisionMode = Field(PrecisionMode.FP16, description="Target precision mode ('fp32', 'fp16', 'int8')")
    dynamic_quantization: bool = Field(True, description="Enable dynamic INT8 quantization for weight matrices")
    op_types_to_quantize: Optional[List[str]] = Field(None, description="Specific ONNX operator types to quantize (e.g. ['MatMul', 'Gemm'])")


class ModelQuantizer:
    """
    ONNX Model Quantization Engine for RT-DETR, SLANet, and LaTeX-OCR ONNX models.
    Supports FP16 cast optimization and INT8 dynamic weight quantization.
    """

    @classmethod
    def get_quantized_path(cls, model_path: Union[str, Path], precision: PrecisionMode) -> Path:
        """Return target file path for quantized model variant."""
        p = Path(model_path)
        if precision == PrecisionMode.FP16:
            return p.with_name(f"{p.stem}_fp16{p.suffix}")
        elif precision == PrecisionMode.INT8:
            return p.with_name(f"{p.stem}_int8{p.suffix}")
        return p

    @classmethod
    def quantize_onnx_model(
        cls,
        model_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        config: Optional[QuantizationConfig] = None,
    ) -> Path:
        """
        Quantize ONNX model to FP16 or INT8 precision.
        Falls back gracefully to original model path if ONNX quantization runtime is unavailable.
        """
        cfg = config or QuantizationConfig()
        src_p = Path(model_path)
        target_p = Path(output_path) if output_path else cls.get_quantized_path(src_p, cfg.precision)

        if cfg.precision == PrecisionMode.FP32 or not src_p.exists():
            return src_p

        if target_p.exists():
            logger.debug("Using cached quantized model artifact at '%s'", target_p)
            return target_p

        try:
            if cfg.precision == PrecisionMode.INT8:
                try:
                    from onnxruntime.quantization import QuantType, quantize_dynamic  # type: ignore
                    logger.info("Applying INT8 dynamic quantization to '%s'", src_p)
                    quantize_dynamic(
                        model_input=str(src_p),
                        model_output=str(target_p),
                        weight_type=QuantType.QUInt8,
                    )
                    return target_p
                except ImportError:
                    logger.warning("onnxruntime.quantization unavailable. Skipping INT8 quantization.")

            elif cfg.precision == PrecisionMode.FP16:
                try:
                    import onnx  # type: ignore
                    from onnxconverter_common import float16  # type: ignore
                    logger.info("Converting ONNX model to FP16 at '%s'", src_p)
                    model = onnx.load(str(src_p))
                    model_fp16 = float16.convert_float_to_float16(model)
                    onnx.save(model_fp16, str(target_p))
                    return target_p
                except ImportError:
                    logger.warning("onnxconverter_common unavailable. Skipping FP16 conversion.")

        except Exception as e:
            logger.warning("Quantization failed for '%s': %s. Returning original model.", src_p, e)

        return src_p
