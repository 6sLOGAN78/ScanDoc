"""
Terminal File & Directory Browser Screen for scanDOC TUI.
"""

from pathlib import Path
from typing import List, Tuple
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from scandoc.tui.state import TuiState


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def render_file_picker_screen(
    state: TuiState,
    items: List[Tuple[Path, bool, int, str]],
    selected_idx: int = 0,
) -> Panel:
    """Render terminal file/folder browser screen."""
    table = Table(show_header=True, box=None, padding=(0, 1))
    table.add_column("Sel", width=3)
    table.add_column("Name", style="bold white")
    table.add_column("Format", style="dim cyan", justify="center", width=10)
    table.add_column("Size", style="dim green", justify="right", width=12)

    for i, (path, is_dir, size_bytes, fmt_desc) in enumerate(items):
        is_sel = path in state.selected_paths
        sel_str = "[✓]" if is_sel else "[ ]"
        icon = "📁 " if is_dir else "📄 "
        name_str = f"{icon}{path.name}"
        
        style = "bold yellow reverse" if i == selected_idx else ("bold cyan" if is_dir else "white")
        size_str = "" if is_dir else format_file_size(size_bytes)
        
        table.add_row(sel_str, f"{'› ' if i == selected_idx else '  '}{name_str}", fmt_desc, size_str, style=style)

    subtitle = "Enter: open/select | Space: toggle multi-select | /: search | Backspace: parent dir | Esc: back"
    if state.search_query:
        subtitle += f" | Filter: '{state.search_query}'"

    return Panel(
        table,
        title=f"[bold blue]Select Document or Folder[/bold blue] — [dim]{state.current_dir}[/dim]",
        subtitle=subtitle,
        border_style="cyan",
        padding=(1, 2),
    )
