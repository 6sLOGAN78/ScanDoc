"""
CLI command handler for 'scandoc tui' interactive terminal UI.
"""

import os
import shutil
import subprocess
import sys
from typing import Any

from scandoc.cli.exceptions import CliError
from scandoc.cli.taxonomy import ExitCode
from scandoc.tui import run_tui_app


def run_tui(args: Any) -> ExitCode:
    """
    Launch interactive scanDOC Terminal UI (TUI).
    Integrates native Go TUI binary when built or available on PATH.
    """
    # Check for native Go binary executable
    go_binary = shutil.which("scandoc-tui")
    if not go_binary:
        local_go_bin = os.path.join(os.getcwd(), "scandoc-tui")
        if os.path.exists(local_go_bin) and os.access(local_go_bin, os.X_OK):
            go_binary = local_go_bin

    if go_binary:
        try:
            res = subprocess.run([go_binary])
            return ExitCode(res.returncode)
        except Exception as e:
            pass

    try:
        res = run_tui_app()
        return ExitCode.SUCCESS
    except Exception as e:
        raise CliError(f"TUI execution error: {e}", exit_code=ExitCode.INTERNAL_ERROR)
