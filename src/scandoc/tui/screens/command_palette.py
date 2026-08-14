"""
Claude-Code-Style Command Palette Screen renderer for scanDOC TUI.
"""

from typing import List, Tuple
from rich.panel import Panel
from rich.table import Table

from scandoc.tui.state import ScreenType, TuiState

COMMAND_PALETTE_ITEMS: List[Tuple[str, str, str]] = [
    ("Open File Picker", "Browse and select single or multiple documents", ScreenType.FILE_PICKER),
    ("Open Folder Directory", "Select an entire directory folder for batch processing", ScreenType.FOLDER_PICKER),
    ("Configure Pipeline", "Edit OCR, Layout, Table, Formula, and VLM pipeline stages", ScreenType.PIPELINE_CONFIG),
    ("Run Document Pipeline", "Execute processing on currently selected documents", ScreenType.PROCESSING),
    ("Inspect DocumentIR", "View document structure, pages, blocks, tables, formulas", ScreenType.DOCUMENT_INSPECTOR),
    ("Export Document", "Export to Markdown, HTML, JSON, DOCX, EPUB, PDF/A, RAG", ScreenType.EXPORT),
    ("Manage Models", "List, download, verify, or clear ML model weights", ScreenType.MODEL_MANAGER),
    ("Run Benchmarks", "Compare scanDOC accuracy and latency against Docling", ScreenType.BENCHMARK),
    ("Manage REST Server", "Start/Stop local REST API and Studio server", ScreenType.SERVER_MANAGER),
    ("System Settings", "View offline status, default devices, masked API keys", ScreenType.SETTINGS),
    ("View Help", "Show keyboard shortcuts and quick reference", ScreenType.HELP),
]


def render_command_palette_screen(state: TuiState, selected_idx: int = 0) -> Panel:
    """Render Claude-Code-style Command Palette modal."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Command", style="bold white", width=26)
    table.add_column("Description", style="dim green")

    query = state.search_query.lower()
    filtered = [
        item for item in COMMAND_PALETTE_ITEMS
        if not query or query in item[0].lower() or query in item[1].lower()
    ]

    for i, (title, desc, _) in enumerate(filtered):
        prefix = "› " if i == selected_idx else "  "
        style = "bold yellow reverse" if i == selected_idx else "white"
        table.add_row(f"{prefix}{title}", desc, style=style)

    subtitle = "Type to search | Enter: Execute Action | Esc: Close Palette"

    return Panel(
        table,
        title="[bold yellow]Command Palette[/bold yellow] — [dim]> type a command...[/dim]",
        subtitle=subtitle,
        border_style="yellow",
        padding=(1, 2),
    )
