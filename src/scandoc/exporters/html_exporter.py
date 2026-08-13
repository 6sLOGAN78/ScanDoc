"""
HtmlExporter serializing DocumentIR into structured semantic HTML5 documents.
"""

from typing import List, Optional

from scandoc.exporters.asset_resolver import AssetResolver
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


class HtmlExporter(BaseExporter):
    """
    Exporter converting DocumentIR into semantic HTML documents.
    """

    @property
    def format_id(self) -> str:
        return "html"

    @property
    def description(self) -> str:
        return "HTML5 Format Exporter"

    def export(
        self,
        document: DocumentIR,
        options: Optional[ExportOptions] = None,
    ) -> ExportResult:
        opts = options or ExportOptions(format_id="html")
        lines: List[str] = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            '  <meta charset="utf-8">',
            f'  <title>{document.metadata.name or "Document"}</title>',
            "</head>",
            "<body>",
        ]
        warnings: List[str] = []
        asset_refs: List[str] = []

        # Metadata Header
        if opts.include_metadata and document.metadata:
            meta = document.metadata
            lines.append('  <header class="document-header">')
            lines.append(f'    <h1>{meta.name or "Document"}</h1>')
            if meta.author:
                lines.append(f"    <p><strong>Author:</strong> {meta.author}</p>")
            lines.append("  </header>")

        lines.append('  <main class="document-body">')

        for page in document.pages:
            lines.append(f'    <section class="page" data-page-index="{page.page_index}">')
            for block in page.blocks:
                prov_attr = ""
                if opts.include_provenance and hasattr(block, "provenance") and block.provenance:
                    prov = block.provenance
                    prov_attr = f' data-provider="{prov.provider}" data-stage="{prov.stage}"'

                if isinstance(block, HeadingBlock):
                    tag = f"h{max(1, min(6, block.level))}"
                    lines.append(f'      <{tag}{prov_attr}>{block.text}</{tag}>')

                elif isinstance(block, ParagraphBlock):
                    lines.append(f'      <p{prov_attr}>{block.text}</p>')

                elif isinstance(block, ListBlock):
                    is_ord = getattr(block, "ordered", getattr(block, "is_ordered", False))
                    tag = "ol" if is_ord else "ul"
                    lines.append(f"      <{tag}{prov_attr}>")
                    for item in block.items:
                        item_txt = getattr(item, "text", str(item))
                        lines.append(f"        <li>{item_txt}</li>")
                    lines.append(f"      </{tag}>")

                elif isinstance(block, TableBlock):
                    lines.append(f"      <table{prov_attr}>")
                    lines.append("        <tbody>")
                    grid = [["" for _ in range(block.num_cols)] for _ in range(block.num_rows)]
                    for cell in block.cells:
                        if cell.row_index < block.num_rows and cell.col_index < block.num_cols:
                            grid[cell.row_index][cell.col_index] = cell.text or ""
                    for row in grid:
                        lines.append("          <tr>")
                        for cell_txt in row:
                            lines.append(f"            <td>{cell_txt}</td>")
                        lines.append("          </tr>")
                    lines.append("        </tbody>")
                    lines.append("      </table>")

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
                    lines.append(f"      <figure{prov_attr}>")
                    lines.append(f'        <img src="{src}" alt="{block.id}">')
                    if block.caption:
                        lines.append(f"        <figcaption>{block.caption}</figcaption>")
                    lines.append("      </figure>")

                elif isinstance(block, FormulaBlock):
                    lines.append(f'      <div class="formula"{prov_attr}>$${block.expression}$$</div>')

                else:
                    text = getattr(block, "text", str(block))
                    lines.append(f"      <div{prov_attr}>{text}</div>")

            lines.append("    </section>")

        lines.append("  </main>")
        lines.append("</body>")
        lines.append("</html>")

        content_str = "\n".join(lines)

        output_path = opts.output_path
        if opts.destination == OutputDestination.FILE_PATH and output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content_str)

        return ExportResult(
            format_id="html",
            destination=opts.destination,
            content=content_str if opts.destination != OutputDestination.BYTES else content_str.encode("utf-8"),
            output_path=output_path,
            warnings=warnings,
            asset_references=asset_refs,
        )
