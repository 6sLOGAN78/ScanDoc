"""
MarkdownExporter serializing DocumentIR into structured Markdown documents.
"""

from typing import List, Optional

from scandoc.exporters.asset_resolver import AssetResolver
from scandoc.exporters.base import BaseExporter
from scandoc.exporters.models import ExportOptions, ExportResult
from scandoc.exporters.taxonomy import OutputDestination
from scandoc.models import DocumentIR, Page
from scandoc.models.blocks import (
    FigureBlock,
    FormulaBlock,
    HeadingBlock,
    ListBlock,
    ParagraphBlock,
    TableBlock,
)


class MarkdownExporter(BaseExporter):
    """
    Exporter converting DocumentIR into Markdown documents.
    """

    @property
    def format_id(self) -> str:
        return "markdown"

    @property
    def description(self) -> str:
        return "Markdown Format Exporter"

    def export(
        self,
        document: DocumentIR,
        options: Optional[ExportOptions] = None,
    ) -> ExportResult:
        opts = options or ExportOptions(format_id="markdown")
        lines: List[str] = []
        warnings: List[str] = []
        asset_refs: List[str] = []

        # 1. Document Metadata Header
        if opts.include_metadata and document.metadata:
            meta = document.metadata
            lines.append(f"# {meta.name or 'Document'}")
            if meta.author:
                lines.append(f"**Author:** {meta.author}")
            if hasattr(meta, "created_at") and meta.created_at:
                lines.append(f"**Date:** {meta.created_at}")
            lines.append("")

        # 2. Iterate Pages & Blocks in Reading Order
        for page in document.pages:
            for block in page.blocks:
                # Add Provenance metadata comment if enabled
                if opts.include_provenance and hasattr(block, "provenance") and block.provenance:
                    prov = block.provenance
                    stg = prov.stage.value if hasattr(prov.stage, "value") else str(prov.stage)
                    lines.append(f"<!-- provenance: provider={prov.provider} stage={stg} -->")

                # Block Type Rendering
                if isinstance(block, HeadingBlock):
                    prefix = "#" * max(1, min(6, block.level))
                    lines.append(f"{prefix} {block.text}")
                    lines.append("")

                elif isinstance(block, ParagraphBlock):
                    lines.append(block.text)
                    lines.append("")

                elif isinstance(block, ListBlock):
                    for item in block.items:
                        item_text = item.text if hasattr(item, "text") else str(item)
                        bullet = "1." if block.ordered else "-"
                        lines.append(f"{bullet} {item_text}")
                    lines.append("")

                elif isinstance(block, TableBlock):
                    tbl_lines, tbl_warn = self._render_table(block, opts)
                    lines.extend(tbl_lines)
                    lines.append("")
                    if tbl_warn:
                        warnings.append(tbl_warn)

                elif isinstance(block, FigureBlock):
                    img_bytes = None
                    if hasattr(block, "image_ref") and block.image_ref and block.image_ref.base64_data:
                        import base64
                        img_bytes = base64.b64decode(block.image_ref.base64_data)
                    else:
                        img_bytes = getattr(block, "image_bytes", None)

                    src, asset_path = AssetResolver.resolve_image_asset(
                        img_bytes, block.id, opts
                    )
                    if asset_path:
                        asset_refs.append(asset_path)
                    lines.append(f"![{block.id}]({src})")
                    if block.caption:
                        lines.append(f"*{block.caption}*")
                    lines.append("")

                elif isinstance(block, FormulaBlock):
                    lines.append(f"$$\n{block.expression}\n$$")
                    lines.append("")

                else:
                    text = getattr(block, "text", str(block))
                    lines.append(text)
                    lines.append("")

        content_str = "\n".join(lines)

        output_path = opts.output_path
        if opts.destination == OutputDestination.FILE_PATH and output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content_str)

        return ExportResult(
            format_id="markdown",
            destination=opts.destination,
            content=content_str if opts.destination != OutputDestination.BYTES else content_str.encode("utf-8"),
            output_path=output_path,
            warnings=warnings,
            asset_references=asset_refs,
        )

    def _render_table(self, table: TableBlock, options: ExportOptions) -> tuple[List[str], Optional[str]]:
        """Render table block to Markdown table or HTML table fallback."""
        lines = []
        has_merged = any(getattr(cell, "row_span", getattr(cell, "rowspan", 1)) > 1 or getattr(cell, "col_span", getattr(cell, "colspan", 1)) > 1 for cell in table.cells)

        grid = [["" for _ in range(table.num_cols)] for _ in range(table.num_rows)]
        for cell in table.cells:
            if cell.row_index < table.num_rows and cell.col_index < table.num_cols:
                grid[cell.row_index][cell.col_index] = cell.text or ""

        if has_merged and options.table_fallback_html:
            # Fallback to HTML table syntax for merged cells
            lines.append("<table>")
            lines.append("  <tbody>")
            for row in grid:
                lines.append("    <tr>")
                for cell_txt in row:
                    lines.append(f"      <td>{cell_txt}</td>")
                lines.append("    </tr>")
            lines.append("  </tbody>")
            lines.append("</table>")
            return lines, "Table contains merged cells; rendered using embedded HTML table syntax fallback."

        if not grid:
            return ["*Empty Table*"], None

        # Header Row
        header_row = grid[0]
        lines.append("| " + " | ".join(header_row) + " |")
        lines.append("| " + " | ".join(["---"] * len(header_row)) + " |")

        # Body Rows
        for row in grid[1:]:
            lines.append("| " + " | ".join(row) + " |")

        warn = "Markdown table cannot preserve merged cell spans natively." if has_merged else None
        return lines, warn
