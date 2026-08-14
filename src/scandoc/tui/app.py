"""
Main Interactive TUI Application for scanDOC.
"""

import os
import select
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


def get_key_input() -> str:
    """
    Read single keypress or line input from terminal cleanly across platforms.
    """
    if sys.stdin.isatty():
        try:
            if os.name == "nt":
                import msvcrt
                ch = msvcrt.getch().decode("utf-8", errors="ignore")
                if ch in ("\r", "\n"):
                    return "enter"
                if ch == "\x1b":
                    return "esc"
                if ch in ("\x08", "\x7f"):
                    return "backspace"
                return ch.lower()
            else:
                import termios
                import tty
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(fd)
                    ch = sys.stdin.read(1)
                    if ch == "\x1b":
                        r, _, _ = select.select([sys.stdin], [], [], 0.05)
                        if r:
                            ch2 = sys.stdin.read(1)
                            if ch2 == "[":
                                ch3 = sys.stdin.read(1)
                                if ch3 == "A": return "up"
                                if ch3 == "B": return "down"
                                if ch3 == "C": return "right"
                                if ch3 == "D": return "left"
                        return "esc"
                    if ch in ("\r", "\n"): return "enter"
                    if ch in ("\x7f", "\x08"): return "backspace"
                    if ch == "\x03": return "ctrl+c"
                    if ch == "\x10": return "ctrl+p"
                    if ch == " ": return "space"
                    return ch.lower()
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception:
            pass

    try:
        raw = input("scanDOC> ").strip()
        return raw.lower()
    except (EOFError, KeyboardInterrupt):
        return "q"


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
        home_menu_count = 10

        while True:
            try:
                self.console.clear()
                self.console.print(self.render_current_screen())

                key = get_key_input()
                scr = self.state.current_screen

                if key in ("q", "ctrl+c"):
                    if scr == ScreenType.HOME:
                        self.console.clear()
                        self.console.print("[bold green]scanDOC TUI session ended. Goodbye![/bold green]")
                        return 0
                    else:
                        self.state.navigate_to(ScreenType.HOME)
                        self.selected_idx = 0
                        continue

                if key == "esc":
                    self.state.navigate_to(ScreenType.HOME)
                    self.selected_idx = 0
                    continue

                if key == "ctrl+p" or key == ">":
                    self.state.navigate_to(ScreenType.COMMAND_PALETTE)
                    self.selected_idx = 0
                    continue

                # SCREEN Specific Navigation
                if scr == ScreenType.HOME:
                    if key in ("w", "k", "up"):
                        self.selected_idx = (self.selected_idx - 1) % home_menu_count
                    elif key in ("s", "j", "down"):
                        self.selected_idx = (self.selected_idx + 1) % home_menu_count
                    elif key in ("1", "o"):
                        self.selected_idx = 0
                        self.state.navigate_to(ScreenType.FILE_PICKER)
                    elif key in ("2", "f"):
                        self.selected_idx = 0
                        self.state.navigate_to(ScreenType.FOLDER_PICKER)
                    elif key == "3":
                        self.selected_idx = 0
                        self.state.navigate_to(ScreenType.DOCUMENT_INSPECTOR)
                    elif key in ("4", "m"):
                        self.selected_idx = 0
                        self.state.navigate_to(ScreenType.MODEL_MANAGER)
                    elif key in ("5", "p"):
                        self.selected_idx = 0
                        self.state.navigate_to(ScreenType.PIPELINE_CONFIG)
                    elif key in ("6", "b"):
                        self.selected_idx = 0
                        self.state.navigate_to(ScreenType.BENCHMARK)
                    elif key in ("7", "s"):
                        self.selected_idx = 0
                        self.state.navigate_to(ScreenType.SERVER_MANAGER)
                    elif key in ("8", "g"):
                        self.selected_idx = 0
                        self.state.navigate_to(ScreenType.SETTINGS)
                    elif key in ("9", "?", "h"):
                        self.selected_idx = 0
                        self.state.navigate_to(ScreenType.HELP)
                    elif key == "0":
                        return 0
                    elif key == "enter":
                        target_map = {
                            0: ScreenType.FILE_PICKER,
                            1: ScreenType.FOLDER_PICKER,
                            2: ScreenType.DOCUMENT_INSPECTOR,
                            3: ScreenType.MODEL_MANAGER,
                            4: ScreenType.PIPELINE_CONFIG,
                            5: ScreenType.BENCHMARK,
                            6: ScreenType.SERVER_MANAGER,
                            7: ScreenType.SETTINGS,
                            8: ScreenType.HELP,
                            9: None,
                        }
                        target = target_map.get(self.selected_idx)
                        if target:
                            self.state.navigate_to(target)
                            self.selected_idx = 0
                        else:
                            return 0

                elif scr in (ScreenType.FILE_PICKER, ScreenType.FOLDER_PICKER):
                    items = self.controller.list_directory_files()
                    max_items = max(1, len(items))
                    if key in ("w", "k", "up"):
                        self.selected_idx = (self.selected_idx - 1) % max_items
                    elif key in ("s", "j", "down"):
                        self.selected_idx = (self.selected_idx + 1) % max_items
                    elif key == "space" and items:
                        target_path = items[self.selected_idx][0]
                        if target_path in self.state.selected_paths:
                            self.state.selected_paths.remove(target_path)
                        else:
                            self.state.selected_paths.append(target_path)
                    elif key == "enter" and items:
                        target_path, is_dir, _, _ = items[self.selected_idx]
                        if is_dir:
                            self.state.current_dir = target_path
                            self.selected_idx = 0
                        else:
                            self.state.selected_paths = [target_path]
                            self.state.active_document_path = target_path
                            self.state.navigate_to(ScreenType.PROCESSING)
                    elif key in ("backspace", "b"):
                        self.state.current_dir = self.state.current_dir.parent
                        self.selected_idx = 0

                elif scr == ScreenType.PIPELINE_CONFIG:
                    if key in ("w", "k", "up"):
                        self.selected_idx = (self.selected_idx - 1) % 9
                    elif key in ("s", "j", "down"):
                        self.selected_idx = (self.selected_idx + 1) % 9
                    elif key in ("space", "enter", "1", "2", "3", "4", "5", "6", "7", "8", "9"):
                        if key == "9" or self.selected_idx == 8:
                            self.controller.toggle_offline_mode()
                        elif self.selected_idx == 6 or key == "7":
                            self.state.pipeline_config.enable_vlm_fallback = not self.state.pipeline_config.enable_vlm_fallback
                        elif self.selected_idx == 7 or key == "8":
                            curr = self.state.pipeline_config.routing_mode
                            modes = ["adaptive", "fast", "deep", "fallback"]
                            nxt = modes[(modes.index(curr) + 1) % len(modes)]
                            self.state.pipeline_config.routing_mode = nxt
                    elif key == "p":
                        self.state.navigate_to(ScreenType.PROCESSING)

                elif scr == ScreenType.MODEL_MANAGER:
                    models = self.controller.list_models_status()
                    max_m = max(1, len(models))
                    if key in ("w", "k", "up"):
                        self.selected_idx = (self.selected_idx - 1) % max_m
                    elif key in ("s", "j", "down"):
                        self.selected_idx = (self.selected_idx + 1) % max_m
                    elif key in ("d", "enter") and models:
                        target_m = models[self.selected_idx]["model_id"]
                        self.controller.download_model(target_m)
                    elif key == "c" and models:
                        target_m = models[self.selected_idx]["model_id"]
                        self.controller.clear_model(target_m)

                elif scr == ScreenType.SERVER_MANAGER:
                    if key in ("1", "start"):
                        self.controller.start_server()
                    elif key in ("2", "stop"):
                        self.controller.stop_server()

                elif scr == ScreenType.EXPORT:
                    if key in ("w", "k", "up"):
                        self.selected_idx = (self.selected_idx - 1) % 8
                    elif key in ("s", "j", "down"):
                        self.selected_idx = (self.selected_idx + 1) % 8
                    elif key in ("enter", "space"):
                        formats = ["markdown", "html", "json", "text", "docx", "epub", "pdfa", "rag_json"]
                        fmt = formats[self.selected_idx % len(formats)]
                        if self.state.active_document_path:
                            self.controller.export_document(self.state.active_document_path, fmt)

                elif scr in (ScreenType.HELP, ScreenType.SETTINGS, ScreenType.BENCHMARK, ScreenType.DOCUMENT_INSPECTOR, ScreenType.PROCESSING):
                    if key in ("enter", "space"):
                        self.state.navigate_to(ScreenType.HOME)
                        self.selected_idx = 0

            except Exception as e:
                self.state.add_log(f"UI Event Error: {e}")


def run_tui_app() -> int:
    """Launch scanDOC interactive terminal UI application."""
    app = ScanDocTuiApp()
    return app.run_interactive_loop()
