"""
Processing & Progress Screen renderer for scanDOC TUI.
"""

from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

from scandoc.tui.state import TuiState


def render_processing_screen(state: TuiState) -> Panel:
    """Render real-time document processing screen."""
    doc_name = state.active_document_path.name if state.active_document_path else "Selected Documents"

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Stage", style="bold white", width=24)
    table.add_column("Progress Bar", width=30)
    table.add_column("Pct", style="bold cyan", width=8)

    pct = state.progress_pct
    stages = [
        ("Native Extraction", min(100.0, pct * 1.2)),
        ("OCR Ingestion", min(100.0, pct * 1.0)),
        ("Layout Detection", min(100.0, pct * 0.9)),
        ("Table Structure", min(100.0, pct * 0.8)),
        ("Formula Recognition", min(100.0, pct * 0.7)),
    ]

    for stage_name, stage_pct in stages:
        bar = ProgressBar(total=100.0, completed=stage_pct, width=28)
        table.add_row(stage_name, bar, f"{stage_pct:5.1f}%")

    info_table = Table(show_header=False, box=None, padding=(0, 1))
    info_table.add_row("[bold yellow]Status:[/bold yellow]", state.processing_status.upper())
    info_table.add_row("[bold yellow]Current Stage:[/bold yellow]", state.progress_stage)
    info_table.add_row("[bold yellow]Active Device:[/bold yellow]", state.device_type.value.upper())
    if state.processing_errors:
        info_table.add_row("[bold red]Errors:[/bold red]", "; ".join(state.processing_errors[:2]))

    content = Table.grid(padding=1)
    content.add_row(table)
    content.add_row(info_table)

    subtitle = "Esc: Back | [C]: Cancel Processing | [L]: Toggle Live Logs"

    return Panel(
        content,
        title=f"[bold blue]Processing {doc_name}[/bold blue]",
        subtitle=subtitle,
        border_style="yellow" if state.processing_status == "processing" else "green",
        padding=(1, 2),
    )
