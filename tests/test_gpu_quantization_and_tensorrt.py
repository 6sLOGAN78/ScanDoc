"""
Test suite for Phase 37: Production GPU Acceleration, Quantization & TensorRT.
"""

from pathlib import Path
import pytest

from scandoc.acceleration import (
    DeviceContext,
    DeviceType,
    ExecutionManager,
    ModelQuantizer,
    MultiGpuExecutionPool,
    PrecisionMode,
    QuantizationConfig,
)


def test_model_quantizer_paths_and_fallback(tmp_path):
    """Test ModelQuantizer generating quantized path suffixes and fallback execution."""
    src = tmp_path / "dummy_model.onnx"
    src.write_bytes(b"DUMMY_ONNX_MODEL_BYTES_FOR_QUANTIZATION_TEST")

    fp16_path = ModelQuantizer.get_quantized_path(src, PrecisionMode.FP16)
    assert fp16_path.name == "dummy_model_fp16.onnx"

    int8_path = ModelQuantizer.get_quantized_path(src, PrecisionMode.INT8)
    assert int8_path.name == "dummy_model_int8.onnx"

    # Test quantize_onnx_model returning valid path
    res_p = ModelQuantizer.quantize_onnx_model(src, config=QuantizationConfig(precision=PrecisionMode.FP16))
    assert res_p is not None
    assert isinstance(res_p, Path)


def test_execution_manager_tensorrt_and_openvino_selection():
    """Test ExecutionManager provider lists for TensorRT, OpenVINO, CUDA, and CPU."""
    mgr = ExecutionManager()

    # TensorRT selection
    ctx_trt = mgr.select_device("tensorrt")
    assert isinstance(ctx_trt, DeviceContext)
    assert ctx_trt.device_type in (DeviceType.TENSORRT, DeviceType.CUDA, DeviceType.CPU)

    # OpenVINO selection
    ctx_ov = mgr.select_device("openvino")
    assert isinstance(ctx_ov, DeviceContext)
    assert ctx_ov.device_type in (DeviceType.OPENVINO, DeviceType.CPU)

    # Execution Providers List
    providers = mgr.get_onnx_execution_providers(ctx_trt)
    assert "CPUExecutionProvider" in providers


def test_multi_gpu_execution_pool():
    """Test MultiGpuExecutionPool distributing tasks across GPU devices."""
    pool = MultiGpuExecutionPool(device_indices=[0, 1])
    assert pool.device_indices == [0, 1]

    ctx1 = pool.get_next_device_context()
    assert ctx1.device_index == 0

    ctx2 = pool.get_next_device_context()
    assert ctx2.device_index == 1

    results = pool.map_batch(lambda item, ctx: (item * 2, ctx.device_index), [10, 20, 30, 40])
    assert len(results) == 4
    assert [r[0] for r in results] == [20, 40, 60, 80]

    pool.shutdown()
