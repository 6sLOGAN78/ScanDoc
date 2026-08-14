"""
REST Server Manager Screen renderer for scanDOC TUI.
"""

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from scandoc.tui.state import TuiState


def render_server_screen(state: TuiState) -> Panel:
    """Render REST API & Web Studio server control panel."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Property", style="bold cyan", width=20)
    table.add_column("Value", style="bold white")

    status_str = "[✓] RUNNING" if state.server_running else "[○] STOPPED"
    status_style = "bold green" if state.server_running else "bold red"

    table.add_row("Server Status:", Text(status_str, style=status_style))
    table.add_row("Listen Host:", state.server_host)
    table.add_row("Listen Port:", str(state.server_port))
    table.add_row("REST API Base:", f"http://{state.server_host}:{state.server_port}/v1/convert")
    table.add_row("Studio Web UI:", f"http://{state.server_host}:{state.server_port}/studio")
    table.add_row("OpenAPI Docs:", f"http://{state.server_host}:{state.server_port}/docs")

    subtitle = "Press [S] to Start/Stop Server | Esc: Back"

    return Panel(
        table,
        title="[bold blue]REST API & Studio Web Server Manager[/bold blue]",
        subtitle=subtitle,
        border_style="green" if state.server_running else "blue",
        padding=(1, 2),
    )
