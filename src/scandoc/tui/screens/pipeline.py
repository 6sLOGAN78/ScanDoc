"""
Pipeline Configuration Screen renderer for scanDOC TUI.
"""

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from scandoc.tui.state import TuiState


def render_pipeline_screen(state: TuiState, selected_idx: int = 0) -> Panel:
    """Render interactive pipeline editor screen."""
    cfg = state.pipeline_config

    stages = [
        ("1", "Native PDF Fast-Path", True, "PyPdfium2"),
        ("2", "OCR Ingestion Engine", True, "RapidOCR"),
        ("3", "DocLayNet Layout Detection", True, "RT-DETR"),
        ("4", "Reading Order Analysis", True, "XY-Cut"),
        ("5", "Table Structure Recognition", True, "SLANet"),
        ("6", "Formula Vision Engine", True, "LaTeX-OCR"),
        ("7", "Multimodal VLM Analysis", cfg.enable_vlm_fallback, "SmolVLM"),
        ("8", "Agentic Routing Strategy", True, cfg.routing_mode.upper()),
        ("9", "Offline Mode Toggle", state.is_offline(), "ENABLED" if state.is_offline() else "DISABLED"),
    ]

    table = Table(show_header=True, box=None, padding=(0, 1))
    table.add_column("Key", style="bold cyan", width=4)
    table.add_column("Status", width=8)
    table.add_column("Pipeline Stage", style="bold white")
    table.add_column("Active Provider", style="dim green")

    for i, (key, label, enabled, provider) in enumerate(stages):
        status_str = "[✓] ON" if enabled else "[○] OFF"
        status_style = "bold green" if enabled else "dim red"
        row_style = "bold yellow reverse" if i == selected_idx else "white"

        table.add_row(f"[{key}]", Text(status_str, style=status_style), f"{'› ' if i == selected_idx else '  '}{label}", provider, style=row_style)

    subtitle = "Space/Enter: Toggle Stage | 9: Offline Mode | Esc: Back | [P]: Run Pipeline"

    return Panel(
        table,
        title="[bold blue]Pipeline Configuration Editor[/bold blue]",
        subtitle=subtitle,
        border_style="magenta",
        padding=(1, 2),
    )
