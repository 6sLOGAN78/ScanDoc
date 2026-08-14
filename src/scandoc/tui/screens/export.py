"""
Exporter Screen renderer for scanDOC TUI.
"""

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from scandoc.exporters import default_exporter_registry
from scandoc.tui.state import TuiState


def render_export_screen(state: TuiState, selected_idx: int = 0) -> Panel:
    """Render multi-format export UI screen."""
    exporters = default_exporter_registry.list_exporters()
    fmt_ids = [e.format_id for e in exporters]

    table = Table(show_header=True, box=None, padding=(0, 1))
    table.add_column("Key", style="bold cyan", width=4)
    table.add_column("Format ID", style="bold white", width=14)
    table.add_column("Description", style="dim green")

    for i, exp in enumerate(exporters):
        is_sel = exp.format_id.lower() == state.selected_export_format.lower()
        sel_prefix = "[✓] " if is_sel else "[ ] "
        prefix = "› " if i == selected_idx else "  "
        style = "bold yellow reverse" if i == selected_idx else ("bold cyan" if is_sel else "white")

        table.add_row(f"[{i+1}]", f"{prefix}{sel_prefix}{exp.format_id}", exp.description, style=style)

    opts_table = Table(show_header=False, box=None, padding=(0, 2))
    opts_table.add_row("Output Directory:", str(state.export_output_dir))
    opts_table.add_row("Include Images:", "[✓] YES" if state.include_images else "[ ] NO")
    opts_table.add_row("Preserve Formulas:", "[✓] YES" if state.preserve_formulas else "[ ] NO")
    opts_table.add_row("Preserve Tables:", "[✓] YES" if state.preserve_tables else "[ ] NO")

    content = Table.grid(padding=1)
    content.add_row(table)
    content.add_row(Text("─" * 50, style="dim"))
    content.add_row(opts_table)

    subtitle = "Space/Enter: Select Format | [E]: Trigger Export | Esc: Back"

    return Panel(
        content,
        title="[bold blue]Multi-Format Exporter Studio[/bold blue]",
        subtitle=subtitle,
        border_style="green",
        padding=(1, 2),
    )
