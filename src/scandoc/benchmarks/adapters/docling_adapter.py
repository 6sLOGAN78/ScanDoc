"""
Docling benchmark adapter.
"""

from pathlib import Path
import time
import tracemalloc
from typing import Optional

from scandoc.benchmarks.adapters.base import BaseBenchmarkAdapter
from scandoc.benchmarks.models import BenchmarkConversionResult


class DoclingAdapter(BaseBenchmarkAdapter):
    """
    Adapter for IBM Docling document converter engine.
    """

    def __init__(self):
        self._docling_installed = False
        self._converter = None
        self._version_str = "unavailable"

        try:
            from docling.document_converter import DocumentConverter
            self._converter = DocumentConverter()
            self._docling_installed = True
            
            import docling
            self._version_str = getattr(docling, "__version__", "installed")
        except (ImportError, Exception):
            self._docling_installed = False

    @property
    def name(self) -> str:
        return "docling"

    @property
    def version(self) -> str:
        return self._version_str

    def is_available(self) -> bool:
        return self._docling_installed and self._converter is not None

    def convert(self, file_path: str) -> BenchmarkConversionResult:
        if not self.is_available():
            return BenchmarkConversionResult(
                adapter_name=self.name,
                success=False,
                error_message="Docling dependency unavailable in current environment. Install docling package to run comparison.",
            )

        p = Path(file_path).expanduser().resolve()
        if not p.exists():
            return BenchmarkConversionResult(
                adapter_name=self.name,
                success=False,
                error_message=f"File not found: {file_path}",
            )

        tracemalloc.start()
        t0 = time.perf_counter()

        try:
            result = self._converter.convert(str(p))
            elapsed = time.perf_counter() - t0
            current_mem, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            doc = getattr(result, "document", None)
            extracted_text = ""
            page_count = 1

            if doc:
                # Export text or markdown from Docling document model
                if hasattr(doc, "export_to_markdown"):
                    extracted_text = doc.export_to_markdown()
                elif hasattr(doc, "export_to_text"):
                    extracted_text = doc.export_to_text()
                
                if hasattr(doc, "pages"):
                    page_count = len(doc.pages)

            return BenchmarkConversionResult(
                adapter_name=self.name,
                success=True,
                page_count=page_count,
                extracted_text=extracted_text,
                tables=[],
                elements=[],
                latency_sec=round(elapsed, 4),
                peak_ram_mb=round(peak_mem / (1024 * 1024), 2),
            )

        except Exception as exc:
            tracemalloc.stop()
            return BenchmarkConversionResult(
                adapter_name=self.name,
                success=False,
                error_message=f"Docling execution error: {exc}",
                latency_sec=round(time.perf_counter() - t0, 4),
            )
