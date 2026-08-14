"""
Telemetry and server observability metrics endpoint.
"""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/v1", tags=["Telemetry"])


@router.get("/telemetry")
def get_telemetry(request: Request):
    """
    Get server metrics and job execution statistics.
    """
    job_mgr = request.app.state.job_manager
    return {
        "status": "active",
        "telemetry": job_mgr.get_telemetry(),
    }
