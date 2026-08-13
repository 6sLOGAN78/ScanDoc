"""
ExporterRegistry managing global exporter discovery and execution.
"""

import logging
from typing import Dict, List, Optional

from scandoc.exporters.base import BaseExporter
from scandoc.exporters.docx_exporter import DocxExporter
from scandoc.exporters.exceptions import UnsupportedExporterFormatError
from scandoc.exporters.html_exporter import HtmlExporter
from scandoc.exporters.json_exporter import JsonExporter
from scandoc.exporters.markdown_exporter import MarkdownExporter
from scandoc.exporters.models import ExportOptions, ExportResult
from scandoc.exporters.text_exporter import TextExporter
from scandoc.models import DocumentIR

logger = logging.getLogger("scandoc.exporters.registry")


class ExporterRegistry:
    """
    Central registry for DocumentIR exporters.
    """

    def __init__(self, register_defaults: bool = True):
        self._exporters: Dict[str, BaseExporter] = {}
        if register_defaults:
            self.register(MarkdownExporter())
            self.register(HtmlExporter())
            self.register(JsonExporter())
            self.register(TextExporter())
            self.register(DocxExporter())

    def register(self, exporter: BaseExporter) -> None:
        self._exporters[exporter.format_id.lower()] = exporter

    def unregister(self, format_id: str) -> Optional[BaseExporter]:
        return self._exporters.pop(format_id.lower(), None)

    def get_exporter(self, format_id: str) -> BaseExporter:
        fmt = format_id.lower()
        if fmt not in self._exporters:
            raise UnsupportedExporterFormatError(
                f"No exporter registered for format '{format_id}'. Available: {list(self._exporters.keys())}"
            )
        return self._exporters[fmt]

    def list_exporters(self) -> List[BaseExporter]:
        return list(self._exporters.values())

    def export(
        self,
        document: DocumentIR,
        options: Optional[ExportOptions] = None,
    ) -> ExportResult:
        opts = options or ExportOptions(format_id="markdown")
        exporter = self.get_exporter(opts.format_id)
        return exporter.export(document, options=opts)


# Default global instance
default_exporter_registry = ExporterRegistry(register_defaults=True)
