"""
Model Manager Screen renderer for scanDOC TUI.
"""

from typing import Any, Dict, List
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from scandoc.tui.state import TuiState


def render_models_screen(
    state: TuiState,
    models_status: List[Dict[str, Any]],
    selected_idx: int = 0,
) -> Panel:
    """Render Phase 34 Model Manager UI table."""
    table = Table(show_header=True, box=None, padding=(0, 1))
    table.add_column("Key", style="bold cyan", width=4)
    table.add_column("Model ID", style="bold white", width=22)
    table.add_column("Size", style="dim green", justify="right", width=10)
    table.add_column("Status", width=14)
    table.add_column("Device", style="dim cyan", width=8)

    for i, m in enumerate(models_status):
        exists = m.get("exists", False)
        status_str = "[✓] READY" if exists else "[↓] MISSING"
        status_style = "bold green" if exists else "bold yellow"
        size_mb = f"{m.get('size_bytes', 0) / (1024*1024):.1f} MB"

        prefix = "› " if i == selected_idx else "  "
        style = "bold yellow reverse" if i == selected_idx else "white"

        table.add_row(
            f"[{i+1}]",
            f"{prefix}{m.get('model_id')}",
            size_mb,
            Text(status_str, style=status_style),
            state.device_type.value.upper(),
            style=style,
        )

    subtitle = "Enter/[D]: Download Model | [V]: Verify Checksum | [C]: Clear Cache | Esc: Back"
    if state.is_offline():
        subtitle += " | ● OFFLINE MODE (Downloads Blocked)"

    return Panel(
        table,
        title="[bold blue]Autonomous Model Manager[/bold blue]",
        subtitle=subtitle,
        border_style="yellow" if state.is_offline() else "blue",
        padding=(1, 2),
    )
