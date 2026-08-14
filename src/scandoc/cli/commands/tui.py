"""
CLI command handler for 'scandoc tui' interactive terminal UI.
"""

import sys
from typing import Any

from scandoc.cli.exceptions import CliError
from scandoc.cli.taxonomy import ExitCode
from scandoc.tui import run_tui_app


def run_tui(args: Any) -> ExitCode:
    """
    Launch interactive scanDOC Terminal UI (TUI).
    """
    try:
        res = run_tui_app()
        return ExitCode.SUCCESS
    except Exception as e:
        raise CliError(f"TUI execution error: {e}", exit_code=ExitCode.INTERNAL_ERROR)
