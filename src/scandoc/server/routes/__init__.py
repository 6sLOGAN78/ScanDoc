"""
Routes package exports.
"""

from scandoc.server.routes.convert import router as convert_router
from scandoc.server.routes.health import router as health_router
from scandoc.server.routes.jobs import router as jobs_router
from scandoc.server.routes.studio_router import studio_router
from scandoc.server.routes.telemetry import router as telemetry_router

__all__ = [
    "convert_router",
    "health_router",
    "jobs_router",
    "telemetry_router",
    "studio_router",
]
