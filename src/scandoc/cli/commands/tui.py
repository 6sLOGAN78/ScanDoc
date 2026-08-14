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


def run_tui(args: Any) -> ExitCode:
    """
    Launch interactive scanDOC Terminal UI (TUI).
    Integrates native Go TUI binary when built or available on PATH.
    """
    # Check for native Go binary executable
    go_binary = shutil.which("scandoc-tui")
    
    if not go_binary:
        # Check standard build dir from current working directory
        local_build_bin = os.path.join(os.getcwd(), "build", "scandoc-tui")
        # Check from package __file__ location (e.g. if installed in site-packages/scandoc)
        pkg_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pkg_bin = os.path.join(pkg_dir, "build", "scandoc-tui")
        # Fallback to dev workspace
        dev_bin = os.path.expanduser("~/Desktop/scanDOC/build/scandoc-tui")
        
        search_paths = [
            local_build_bin,
            os.path.join(os.getcwd(), "scandoc-tui"),
            pkg_bin,
            dev_bin
        ]
        
        for path in search_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                go_binary = path
                break

    if go_binary:
        try:
            res = subprocess.run([go_binary])
            return ExitCode(res.returncode)
        except Exception as e:
            raise CliError(f"TUI execution error: {e}", exit_code=ExitCode.INTERNAL_ERROR)
    
    raise CliError("Native Go TUI binary (scandoc-tui) not found. Please build it via 'go build -o build/scandoc-tui ./cmd/scandoc'", exit_code=ExitCode.INTERNAL_ERROR)
