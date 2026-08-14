"""
Help Screen renderer for scanDOC TUI.
"""

from rich.panel import Panel
from rich.table import Table

from scandoc.tui.state import TuiState


def render_help_screen(state: TuiState) -> Panel:
    """Render Keyboard Shortcuts & Help reference screen."""
    table = Table(show_header=True, box=None, padding=(0, 2))
    table.add_column("Shortcut", style="bold cyan", width=14)
    table.add_column("Action Description", style="bold white")

    shortcuts = [
        ("q / Esc", "Quit or Return to Previous Screen"),
        ("?", "Open Help & Shortcut Reference"),
        ("slash", "Focus File Search Filter in Browser"),
        ("o", "Open File Picker Screen"),
        ("f", "Open Folder Browser"),
        ("m", "Open Model Manager"),
        ("p", "Open Pipeline Editor"),
        ("b", "Open Benchmarking Dashboard"),
        ("s", "Open REST Server Manager"),
        ("e", "Open Multi-Format Exporter UI"),
        ("l", "Toggle Live Progress Logs"),
        ("Ctrl+P", "Open Claude-Code-Style Command Palette"),
        ("Space", "Toggle Checkbox or Multi-select Items"),
        ("Enter", "Confirm Selection or Execute Action"),
    ]

    for key, desc in shortcuts:
        table.add_row(f"[{key}]", desc)

    return Panel(
        table,
        title="[bold blue]scanDOC TUI Keyboard Shortcuts & Quick Guide[/bold blue]",
        subtitle="Esc: Return to Previous Screen",
        border_style="cyan",
        padding=(1, 2),
    )
