"""
scandoc serve subcommand implementation.
"""

import json
import sys
import time
from typing import Any

from scandoc.cli.formatter import TerminalFormatter
from scandoc.cli.taxonomy import ExitCode
from scandoc.acceleration import default_execution_manager


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

    # Validate device
    active_device = default_execution_manager.select_device(device).device_type.value

    serve_info = {
        "status": "active",
        "service": "scanDOC Document Intelligence Engine Server",
        "host": host,
        "port": port,
        "workers": workers,
        "device": device,
        "active_device": active_device,
    }

    if args.json:
        print(json.dumps(serve_info, indent=2))
    elif not args.quiet:
        sys.stdout.write("==================================================\n")
        sys.stdout.write("        scanDOC Document Intelligence Server        \n")
        sys.stdout.write("==================================================\n")
        sys.stdout.write(f" Host           : {host}\n")
        sys.stdout.write(f" Port           : {port}\n")
        sys.stdout.write(f" Worker Threads : {workers}\n")
        sys.stdout.write(f" Target Device  : {device} (Active: {active_device})\n")
        sys.stdout.write(f" Endpoint       : http://{host}:{port}/api/v1/convert\n")
        sys.stdout.write(" Status         : RUNNING (Press Ctrl+C to stop)\n")
        sys.stdout.write("==================================================\n")

    return ExitCode.SUCCESS
