"""
Settings Screen renderer for scanDOC TUI.
"""

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from scandoc.tui.state import TuiState


def render_settings_screen(state: TuiState) -> Panel:
    """Render scanDOC configuration settings screen with secret masking."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Setting Key", style="bold cyan", width=26)
    table.add_column("Current Setting Value", style="bold white")

    table.add_row("Offline Mode:", "[✓] ENABLED" if state.is_offline() else "[○] DISABLED")
    table.add_row("Default Device:", state.device_type.value.upper())
    table.add_row("Default Export Format:", state.selected_export_format)
    table.add_row("Export Output Directory:", str(state.export_output_dir))
    table.add_row("Parallel Worker Count:", "4 Threads")
    table.add_row("Logging Verbosity Level:", "INFO")
    table.add_row("Remote OpenAI / VLM API Key:", "********")  # Masked secret
    table.add_row("HuggingFace Auth Token:", "********")      # Masked secret

    subtitle = "Press [8] to Toggle Offline Mode | Esc: Back"

    return Panel(
        table,
        title="[bold blue]scanDOC System Settings & Security Config[/bold blue]",
        subtitle=subtitle,
        border_style="magenta",
        padding=(1, 2),
    )
