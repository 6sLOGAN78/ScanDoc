"""
CLI Command handler for 'scandoc studio' Web UI server.
"""

import logging
import sys
from typing import Any
import webbrowser

from scandoc.cli.exceptions import CliError
from scandoc.cli.formatter import TerminalFormatter
from scandoc.cli.taxonomy import ExitCode
from scandoc.server.app import create_app
from scandoc.server.config import ServerConfig

logger = logging.getLogger("scandoc.cli.commands.studio")


def run_studio(args: Any) -> ExitCode:
    """
    Launch embedded scanDOC Web UI Studio server.
    """
    host = getattr(args, "host", "127.0.0.1")
    port = getattr(args, "port", 8000)
    open_browser = getattr(args, "open_browser", True)

    TerminalFormatter.print_banner()
    print(f"🚀 Launching scanDOC Visual Studio Web UI on http://{host}:{port}/studio ...\n")

    if open_browser:
        try:
            webbrowser.open(f"http://{host}:{port}/studio")
        except Exception:
            pass

    try:
        import uvicorn
        cfg = ServerConfig(host=host, port=port)
        app = create_app(cfg)
        uvicorn.run(app, host=host, port=port, log_level="info")
        return ExitCode.SUCCESS
    except ImportError:
        TerminalFormatter.print_error(
            "Studio Server",
            "uvicorn",
            "Uvicorn server dependency missing. Run 'pip install uvicorn'.",
        )
        return ExitCode.MISSING_DEPENDENCY
    except Exception as e:
        logger.error("Studio server failed: %s", e)
        raise CliError(f"Studio server error: {e}", exit_code=ExitCode.INTERNAL_ERROR)
