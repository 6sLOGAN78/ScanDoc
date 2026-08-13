"""
Unit and integration test suite for Phase 8: CPU/GPU/NPU Hardware Execution Engine.
"""

import pytest
from scandoc.acceleration import (
    DeviceContext,
    DeviceType,
    PrecisionMode,
    DeviceDiscovery,
    ExecutionManager,
    CpuExecutionBackend,
    CudaExecutionBackend,
    OpenVinoExecutionBackend,
    TensorRtExecutionBackend,
    BenchmarkRunner,
    BenchmarkReport,
    BackendUnavailableError,
)
from scandoc.providers.ocr import RapidOCRProvider, OcrProviderConfig


def test_device_context_formatting():
    """Test DeviceContext serialization and device string formatting."""
    ctx_cpu = DeviceContext(device_type=DeviceType.CPU, num_threads=4)
    assert ctx_cpu.to_device_string() == "cpu"
    assert ctx_cpu.precision == PrecisionMode.FP32

    ctx_cuda = DeviceContext(device_type=DeviceType.CUDA, device_index=1, precision=PrecisionMode.FP16)
    assert ctx_cuda.to_device_string() == "cuda:1"
    assert ctx_cuda.precision == PrecisionMode.FP16


def test_device_discovery():
    """Test DeviceDiscovery inspecting hardware runtimes."""
    devices = DeviceDiscovery.discover_devices()
    assert len(devices) >= 1

    # CPU is guaranteed to be present
    cpu_dev = next(d for d in devices if d.device_type == DeviceType.CPU)
    assert cpu_dev.num_threads > 0

    # Verification of bool reporting
    assert isinstance(DeviceDiscovery.is_cuda_available(), bool)
    assert isinstance(DeviceDiscovery.is_openvino_available(), bool)
    assert isinstance(DeviceDiscovery.is_tensorrt_available(), bool)
    assert isinstance(DeviceDiscovery.is_mps_available(), bool)


def test_cpu_execution_backend():
    """Test CpuExecutionBackend configuration and inference execution."""
    backend = CpuExecutionBackend()
    backend.initialize(DeviceContext(device_type=DeviceType.CPU, num_threads=2))

    assert backend.backend_name == "cpu"
    assert backend.is_available is True
    assert backend.capabilities.supports_batching is True

    # Test dummy model session inference call
    def mock_model(x):
        return x * 2

    res = backend.run_inference(mock_model, 5)
    assert res == 10


def test_cuda_execution_backend():
    """Test CudaExecutionBackend capability reporting and graceful unavailable error."""
    backend = CudaExecutionBackend()
    assert backend.backend_name == "cuda"
    assert DeviceType.CUDA in backend.capabilities.supported_devices

    if not backend.is_available:
        with pytest.raises(BackendUnavailableError):
            backend.initialize()
    else:
        backend.initialize()
        providers = backend.get_onnx_execution_providers()
        assert providers[0][0] == "CUDAExecutionProvider"


def test_openvino_and_tensorrt_backends():
    """Test OpenVINO and TensorRT backends."""
    openvino_b = OpenVinoExecutionBackend()
    assert openvino_b.backend_name == "openvino"

    tensorrt_b = TensorRtExecutionBackend()
    assert tensorrt_b.backend_name == "tensorrt"


def test_execution_manager_selection_and_session_pool():
    """Test ExecutionManager device selection and session caching."""
    manager = ExecutionManager(register_defaults=True)
    assert len(manager.list_backends()) == 4

    # Test explicit CPU selection
    ctx_cpu = manager.select_device("cpu")
    assert ctx_cpu.device_type == DeviceType.CPU

    # Test auto selection
    ctx_auto = manager.select_device("auto")
    assert ctx_auto is not None

    # Test session pool caching
    call_count = 0
    def build_expensive_session():
        nonlocal call_count
        call_count += 1
        return {"session_handle": 12345}

    s1 = manager.get_or_create_session("model_ocr_v1", build_expensive_session)
    s2 = manager.get_or_create_session("model_ocr_v1", build_expensive_session)

    assert s1 == s2
    assert call_count == 1  # Verify function was called only once!


def test_benchmark_runner():
    """Test BenchmarkRunner latency, throughput, and memory reporting."""
    def dummy_inference(val):
        return [val * i for i in range(100)]

    ctx = DeviceContext(device_type=DeviceType.CPU)
    report: BenchmarkReport = BenchmarkRunner.run_benchmark(
        inference_fn=dummy_inference,
        sample_input=10,
        device_context=ctx,
        num_runs=5,
        warmup_runs=1,
    )

    assert isinstance(report, BenchmarkReport)
    assert report.num_runs == 5
    assert report.mean_latency_ms >= 0.0
    assert report.throughput_fps >= 0.0
    assert report.ram_usage_mb > 0.0


def test_rapidocr_execution_engine_integration():
    """Test RapidOCRProvider integration with ExecutionManager device selection."""
    manager = ExecutionManager()
    dev_ctx = manager.select_device("auto")

    cfg = OcrProviderConfig(provider_name="rapidocr", device=dev_ctx.to_device_string())
    provider = RapidOCRProvider(config=cfg)

    assert provider.provider_id == "rapidocr"
    assert provider.model_id == "PP-OCRv4"
