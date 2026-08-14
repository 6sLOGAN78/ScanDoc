"""
CUDA GPU VRAM and execution telemetry profiler with safe null fallback.
"""

from typing import Dict, Optional


def get_gpu_telemetry() -> Optional[Dict[str, float]]:
    """
    Collect GPU VRAM and device info if PyTorch/CUDA is available.
    Returns None if GPU/CUDA is unavailable.
    """
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            allocated_mb = torch.cuda.memory_allocated(0) / (1024 * 1024)
            reserved_mb = torch.cuda.memory_reserved(0) / (1024 * 1024)
            return {
                "gpu_available": True,
                "vram_allocated_mb": round(allocated_mb, 2),
                "vram_reserved_mb": round(reserved_mb, 2),
            }
    except Exception:
        pass

    return None
