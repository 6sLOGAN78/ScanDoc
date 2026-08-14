"""
Home Screen renderer for scanDOC TUI.
"""

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from scandoc.tui.state import ScreenType, TuiState


MENU_ITEMS = [
    ("1", "Open File", ScreenType.FILE_PICKER),
    ("2", "Open Folder", ScreenType.FOLDER_PICKER),
    ("3", "Recent Documents", ScreenType.DOCUMENT_INSPECTOR),
    ("4", "Model Manager", ScreenType.MODEL_MANAGER),
    ("5", "Pipeline Configuration", ScreenType.PIPELINE_CONFIG),
    ("6", "Benchmark", ScreenType.BENCHMARK),
    ("7", "Server", ScreenType.SERVER_MANAGER),
    ("8", "Settings", ScreenType.SETTINGS),
    ("9", "Help", ScreenType.HELP),
    ("Q", "Quit", "quit"),
]


def render_home_screen(state: TuiState, selected_idx: int = 0) -> Panel:
    """Render Claude-style Home screen menu."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Shortcut", style="bold cyan", width=4)
    table.add_column("Option", style="bold white")

    for i, (key, label, _) in enumerate(MENU_ITEMS):
        prefix = "› " if i == selected_idx else "  "
        style = "bold yellow reverse" if i == selected_idx else "bold white"
        table.add_row(f"[{key}]", f"{prefix}{label}", style=style)

    offline_status = "● OFFLINE MODE" if state.is_offline() else "● ONLINE READY"
    status_color = "yellow" if state.is_offline() else "green"

    footer = Text.assemble(
        ("Local • ", "bold dim"),
        (f"{offline_status} • ", f"bold {status_color}"),
        (f"Device: {state.device_type.value.upper()}", "bold dim"),
    )

    body = Panel(
        table,
        title="[bold blue]scanDOC Document Intelligence Engine[/bold blue] v0.1.0",
        subtitle=footer,
        border_style="blue",
        padding=(1, 2),
    )
    return body
