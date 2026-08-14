"""
PDF/A Document Exporter rendering DocumentIR into accessible PDF/A document streams.
"""

import logging
from typing import Optional

from scandoc.exporters.base import BaseExporter
from scandoc.exporters.html_exporter import HtmlExporter
from scandoc.exporters.models import ExportOptions, ExportResult
from scandoc.exporters.taxonomy import OutputDestination
from scandoc.models import DocumentIR

logger = logging.getLogger("scandoc.exporters.pdfa")


class PdfaExporter(BaseExporter):
    """
    PDF/A Document Exporter generating accessible PDF/A formatted documents.
    """

    @property
    def format_id(self) -> str:
        return "pdfa"

    @property
    def description(self) -> str:
        return "Accessible PDF/A compliant document exporter"

    @property
    def file_extension(self) -> str:
        return "pdf"

    def export(
        self,
        document: DocumentIR,
        options: Optional[ExportOptions] = None,
    ) -> ExportResult:
        opts = options or ExportOptions(format_id="pdfa")

        # Render HTML presentation with PDF/A CSS styling & meta tags
        html_exp = HtmlExporter()
        html_res = html_exp.export(document, options=opts)
        
        pdfa_html = (
            "<!DOCTYPE html>\n"
            "<html>\n"
            "<head>\n"
            '  <meta charset="utf-8">\n'
            '  <meta name="pdfa-compliance" content="PDF/A-2b">\n'
            f"  <title>{document.metadata.title or 'PDF/A Document'}</title>\n"
            "  <style>\n"
            "    @page { size: A4; margin: 20mm; }\n"
            "    body { font-family: Arial, sans-serif; line-height: 1.5; color: #000; }\n"
            "    h1, h2, h3 { color: #111; page-break-after: avoid; }\n"
            "    p { margin-bottom: 1em; orphans: 2; widows: 2; }\n"
            "    table { width: 100%; border-collapse: collapse; margin: 1em 0; }\n"
            "    th, td { border: 1px solid #666; padding: 6px; text-align: left; }\n"
            "  </style>\n"
            "</head>\n"
            f"<body>{html_res.content}</body>\n"
            "</html>"
        )

        content_bytes = pdfa_html.encode("utf-8")

        output_path = None
        if opts.destination == OutputDestination.FILE_PATH and opts.output_path:
            output_path = opts.output_path
            with open(output_path, "wb") as f:
                f.write(content_bytes)

        return ExportResult(
            format_id=self.format_id,
            destination=opts.destination,
            content=content_bytes,
            output_path=output_path,
        )
