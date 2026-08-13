"""
TextExporter serializing DocumentIR into plain text files with explicit element placeholders.
"""

from typing import List, Optional

from scandoc.exporters.base import BaseExporter
from scandoc.exporters.models import ExportOptions, ExportResult
from scandoc.exporters.taxonomy import OutputDestination
from scandoc.models import DocumentIR
from scandoc.models.blocks import (
    FigureBlock,
    FormulaBlock,
    HeadingBlock,
    ListBlock,
    ParagraphBlock,
    TableBlock,
)


class TextExporter(BaseExporter):
    """
    Exporter converting DocumentIR into plain text documents.
    """

    @property
    def format_id(self) -> str:
        return "text"

    @property
    def description(self) -> str:
        return "Plain Text Format Exporter"

    def export(
        self,
        document: DocumentIR,
        options: Optional[ExportOptions] = None,
    ) -> ExportResult:
        opts = options or ExportOptions(format_id="text")
        lines: List[str] = []
        warnings: List[str] = []

        if opts.include_metadata and document.metadata:
            lines.append(f"DOCUMENT: {document.metadata.name or 'Document'}")
            lines.append("=" * 40)
            lines.append("")

        for page in document.pages:
            lines.append(f"--- Page {page.page_index + 1} ---")
            for block in page.blocks:
                if isinstance(block, HeadingBlock):
                    lines.append(block.text.upper())
                    lines.append("")

                elif isinstance(block, ParagraphBlock):
                    lines.append(block.text)
                    lines.append("")

                elif isinstance(block, ListBlock):
                    is_ord = getattr(block, "ordered", getattr(block, "is_ordered", False))
                    for item in block.items:
                        item_txt = getattr(item, "text", str(item))
                        bullet = "-" if is_ord else "*"
                        lines.append(f"{bullet} {item_txt}")
                    lines.append("")

                elif isinstance(block, TableBlock):
                    grid = [["" for _ in range(block.num_cols)] for _ in range(block.num_rows)]
                    for cell in block.cells:
                        if cell.row_index < block.num_rows and cell.col_index < block.num_cols:
                            grid[cell.row_index][cell.col_index] = cell.text or ""
                    for row in grid:
                        lines.append(" | ".join(row))
                    lines.append("")

                elif isinstance(block, FigureBlock):
                    fig_id = getattr(block, "id", "figure")
                    lines.append(f"[Figure: {fig_id}]")
                    if block.caption:
                        lines.append(f"Caption: {block.caption}")
                    lines.append("")
                    warnings.append(f"Raster image block '{fig_id}' replaced with text placeholder.")

                elif isinstance(block, FormulaBlock):
                    lines.append(f"Equation: {block.expression}")
                    lines.append("")

                else:
                    lines.append(getattr(block, "text", str(block)))
                    lines.append("")

        content_str = "\n".join(lines)

        output_path = opts.output_path
        if opts.destination == OutputDestination.FILE_PATH and output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content_str)

        return ExportResult(
            format_id="text",
            destination=opts.destination,
            content=content_str if opts.destination != OutputDestination.BYTES else content_str.encode("utf-8"),
            output_path=output_path,
            warnings=warnings,
            asset_references=[],
        )
