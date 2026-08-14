"""
FastAPI Application Factory for scanDOC REST API server.
"""

from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from scandoc.cli.formatter import TerminalFormatter
from scandoc.server.config import ServerConfig
from scandoc.server.jobs import AsyncJobManager
from scandoc.server.routes import convert_router, health_router, jobs_router, studio_router, telemetry_router
from scandoc.server.taxonomy import ServerErrorCode


def create_app(config: Optional[ServerConfig] = None) -> FastAPI:
    """
    Factory function producing a configured, testable FastAPI application instance.
    
    Args:
        config: Optional ServerConfig settings.
        
    Returns:
        FastAPI application instance.
    """
    server_config = config or ServerConfig()
    job_manager = AsyncJobManager(server_config)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        app.state.server_config = server_config
        app.state.job_manager = job_manager
        yield
        # Shutdown
        job_manager.shutdown()

    app = FastAPI(
        title="scanDOC Document Intelligence Engine REST API",
        description="High-performance open-source document conversion and structural intelligence API.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.state.server_config = server_config
    app.state.job_manager = job_manager

    # Attach CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=server_config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API Routers
    app.include_router(health_router)
    app.include_router(convert_router)
    app.include_router(jobs_router)
    app.include_router(telemetry_router)
    app.include_router(studio_router)

    # Global Exception Handler protecting against Python stack trace leakage & secret exposure
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        clean_msg = TerminalFormatter.mask_secrets(str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": ServerErrorCode.INTERNAL_ERROR.value,
                "message": "An unexpected internal server error occurred.",
                "details": {"error": clean_msg},
            },
        )

    return app
