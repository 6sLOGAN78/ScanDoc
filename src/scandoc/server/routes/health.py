"""
Health & Readiness endpoints for scanDOC REST API server.
"""

from fastapi import APIRouter
from scandoc.acceleration import default_execution_manager

router = APIRouter(tags=["Health & Status"])


@router.get("/health")
def get_health():
    """
    Liveness health check endpoint.
    Fast check with zero heavy processing.
    """
    return {"status": "ok"}


@router.get("/ready")
def get_readiness():
    """
    Readiness endpoint indicating engine hardware availability.
    """
    device_ctx = default_execution_manager.select_device("auto")
    return {
        "status": "ready",
        "engine": "scanDOC Document Intelligence Engine",
        "active_device": device_ctx.device_type.value,
        "onnx_providers": getattr(device_ctx, "onnx_execution_providers", []),
    }
