"""
scandoc serve subcommand implementation.
"""

import json
import sys
from typing import Any

from scandoc.acceleration import default_execution_manager
from scandoc.cli.taxonomy import ExitCode
from scandoc.server import ServerConfig, create_app


def run_serve(args: Any) -> int:
    """
    Execute `scandoc serve` subcommand entry point.
    
    Returns:
        int: Exit code (ExitCode.SUCCESS, etc.)
    """
    host = getattr(args, "host", "127.0.0.1")
    port = getattr(args, "port", 8000)
    workers = getattr(args, "workers", 4)
    device = getattr(args, "device", "auto")
    run_app = getattr(args, "run_server", False)

    active_device = default_execution_manager.select_device(device).device_type.value

    server_config = ServerConfig(
        host=host,
        port=port,
        workers=workers,
        device=device,
    )

    serve_info = {
        "status": "active",
        "service": "scanDOC Document Intelligence Engine Server",
        "host": host,
        "port": port,
        "workers": workers,
        "device": device,
        "active_device": active_device,
        "endpoints": {
            "health": f"http://{host}:{port}/health",
            "readiness": f"http://{host}:{port}/ready",
            "openapi": f"http://{host}:{port}/openapi.json",
            "docs": f"http://{host}:{port}/docs",
            "sync_convert": f"http://{host}:{port}/api/v1/convert",
            "async_jobs": f"http://{host}:{port}/api/v1/jobs",
        },
    }

    if getattr(args, "json", False):
        print(json.dumps(serve_info, indent=2))
    elif not getattr(args, "quiet", False):
        sys.stdout.write("==================================================\n")
        sys.stdout.write("        scanDOC Document Intelligence Server        \n")
        sys.stdout.write("==================================================\n")
        sys.stdout.write(f" Host           : {host}\n")
        sys.stdout.write(f" Port           : {port}\n")
        sys.stdout.write(f" Worker Threads : {workers}\n")
        sys.stdout.write(f" Target Device  : {device} (Active: {active_device})\n")
        sys.stdout.write(f" OpenAPI Specs  : http://{host}:{port}/docs\n")
        sys.stdout.write(f" Sync Endpoint  : http://{host}:{port}/api/v1/convert\n")
        sys.stdout.write(f" Async Endpoint : http://{host}:{port}/api/v1/jobs\n")
        sys.stdout.write(" Status         : READY\n")
        sys.stdout.write("==================================================\n")

    if run_app:
        import uvicorn
        app = create_app(server_config)
        uvicorn.run(app, host=host, port=port, log_level="info" if not getattr(args, "quiet", False) else "error")

    return ExitCode.SUCCESS
