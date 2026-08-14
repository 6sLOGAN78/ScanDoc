"""
DocumentIR Inspector Screen renderer for scanDOC TUI.
"""

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from scandoc.models import BlockType
from scandoc.tui.state import TuiState


def render_document_inspector_screen(state: TuiState, selected_idx: int = 0) -> Panel:
    """Render DocumentIR structure inspector screen."""
    ir = state.active_document_ir
    doc_name = state.active_document_path.name if state.active_document_path else "Active Document"

    if not ir:
        return Panel(
            Text("No document processed yet. Select a document and run the pipeline to inspect structure.", style="dim yellow"),
            title="[bold blue]Document Inspector[/bold blue]",
            subtitle="Esc: Back | [O]: Open File Picker",
            border_style="blue",
            padding=(2, 2),
        )

    # Compute block statistics
    num_pages = len(ir.pages)
    all_blocks = [b for p in ir.pages for b in p.blocks]
    num_text = sum(1 for b in all_blocks if getattr(b, "type", getattr(b, "block_type", None)) == BlockType.TEXT)
    num_tables = sum(1 for b in all_blocks if getattr(b, "type", getattr(b, "block_type", None)) == BlockType.TABLE)
    num_formulas = sum(1 for b in all_blocks if getattr(b, "type", getattr(b, "block_type", None)) == BlockType.FORMULA)
    num_figures = sum(1 for b in all_blocks if getattr(b, "type", getattr(b, "block_type", None)) == BlockType.FIGURE)

    stats_table = Table(show_header=False, box=None, padding=(0, 2))
    stats_table.add_column("Metric", style="bold cyan")
    stats_table.add_column("Value", style="bold yellow", justify="right")
    stats_table.add_row("Pages", str(num_pages))
    stats_table.add_row("Text Blocks", str(num_text))
    stats_table.add_row("Tables", str(num_tables))
    stats_table.add_row("Formulas", str(num_formulas))
    stats_table.add_row("Figures", str(num_figures))
    stats_table.add_row("Total Structural Elements", str(len(all_blocks)))

    inspector_options = [
        ("1", "Page Structure View"),
        ("2", "Text Blocks View"),
        ("3", "Tables & Cell Matrices"),
        ("4", "Formulas & LaTeX"),
        ("5", "Figures & VLM Descriptions"),
        ("6", "Provenance & Confidence"),
        ("7", "Raw DocumentIR JSON Payload"),
    ]

    opts_table = Table(show_header=False, box=None, padding=(0, 2))
    opts_table.add_column("Key", style="bold cyan", width=4)
    opts_table.add_column("View", style="bold white")

    for i, (key, label) in enumerate(inspector_options):
        prefix = "› " if i == selected_idx else "  "
        style = "bold yellow reverse" if i == selected_idx else "bold white"
        opts_table.add_row(f"[{key}]", f"{prefix}{label}", style=style)

    content = Table.grid(padding=1)
    content.add_row(stats_table)
    content.add_row(Text("─" * 45, style="dim"))
    content.add_row(opts_table)

    subtitle = "Enter: Select View | [E]: Export Document | Esc: Back"

    return Panel(
        content,
        title=f"[bold blue]Document Inspector — {doc_name}[/bold blue]",
        subtitle=subtitle,
        border_style="green",
        padding=(1, 2),
    )
