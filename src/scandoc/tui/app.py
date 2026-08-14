"""
Main Interactive TUI Application for scanDOC.
"""

import os
import sys
import time
from typing import Optional

from rich.console import Console

from scandoc.tui.controller import TuiController
from scandoc.tui.screens import (
    render_benchmark_screen,
    render_command_palette_screen,
    render_document_inspector_screen,
    render_export_screen,
    render_file_picker_screen,
    render_help_screen,
    render_home_screen,
    render_models_screen,
    render_pipeline_screen,
    render_processing_screen,
    render_server_screen,
    render_settings_screen,
)
from scandoc.tui.state import ScreenType, TuiState


class ScanDocTuiApp:
    """
    Claude-Style Interactive Terminal UI Application for scanDOC.
    """

    def __init__(self, controller: Optional[TuiController] = None):
        self.controller = controller or TuiController()
        self.state = self.controller.state
        self.console = Console()
        self.selected_idx = 0

    def render_current_screen(self):
        """Render panel object for active screen state."""
        scr = self.state.current_screen

        if scr == ScreenType.HOME:
            return render_home_screen(self.state, selected_idx=self.selected_idx)
        elif scr in (ScreenType.FILE_PICKER, ScreenType.FOLDER_PICKER):
            items = self.controller.list_directory_files()
            return render_file_picker_screen(self.state, items, selected_idx=self.selected_idx)
        elif scr == ScreenType.PIPELINE_CONFIG:
            return render_pipeline_screen(self.state, selected_idx=self.selected_idx)
        elif scr == ScreenType.PROCESSING:
            return render_processing_screen(self.state)
        elif scr == ScreenType.DOCUMENT_INSPECTOR:
            return render_document_inspector_screen(self.state, selected_idx=self.selected_idx)
        elif scr == ScreenType.EXPORT:
            return render_export_screen(self.state, selected_idx=self.selected_idx)
        elif scr == ScreenType.MODEL_MANAGER:
            models_status = self.controller.list_models_status()
            return render_models_screen(self.state, models_status, selected_idx=self.selected_idx)
        elif scr == ScreenType.BENCHMARK:
            return render_benchmark_screen(self.state)
        elif scr == ScreenType.SERVER_MANAGER:
            return render_server_screen(self.state)
        elif scr == ScreenType.SETTINGS:
            return render_settings_screen(self.state)
        elif scr == ScreenType.HELP:
            return render_help_screen(self.state)
        elif scr == ScreenType.COMMAND_PALETTE:
            return render_command_palette_screen(self.state, selected_idx=self.selected_idx)
        else:
            return render_home_screen(self.state, selected_idx=self.selected_idx)

    def run_interactive_loop(self) -> int:
        """Run terminal UI interactive event loop."""
        self.console.clear()
        self.console.print(self.render_current_screen())
        return 0


def run_tui_app() -> int:
    """Launch scanDOC interactive terminal UI application."""
    app = ScanDocTuiApp()
    return app.run_interactive_loop()
