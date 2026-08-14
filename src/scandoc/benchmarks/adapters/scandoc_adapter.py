"""
scanDOC native benchmark adapter.
"""

from pathlib import Path
from typing import Optional
import time
import tracemalloc

from scandoc.benchmarks.adapters.base import BaseBenchmarkAdapter
from scandoc.benchmarks.models import BenchmarkConversionResult
from scandoc.exporters import default_exporter_registry, ExportOptions
from scandoc.pipelines import DocumentPipeline, PipelineConfig, OrderingMode


class ScanDocAdapter(BaseBenchmarkAdapter):
    """
    Adapter for scanDOC Document Intelligence Engine.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self._config = config or PipelineConfig(max_workers=1, ordering_mode=OrderingMode.ORDERED)
        self._pipeline = DocumentPipeline(config=self._config)

    @property
    def name(self) -> str:
        return "scandoc"

    @property
    def version(self) -> str:
        return "0.1.0"

    def is_available(self) -> bool:
        return True

    def convert(self, file_path: str) -> BenchmarkConversionResult:
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
            p_result = self._pipeline.process(p)
            elapsed = time.perf_counter() - t0
            current_mem, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            if p_result.status != "success" or not p_result.document_ir:
                err = "; ".join(p_result.errors) if p_result.errors else "scanDOC conversion failed"
                return BenchmarkConversionResult(
                    adapter_name=self.name,
                    success=False,
                    error_message=err,
                    latency_sec=round(elapsed, 4),
                    peak_ram_mb=round(peak_mem / (1024 * 1024), 2),
                )

            # Export text
            exp_res = default_exporter_registry.export(p_result.document_ir, ExportOptions(format_id="text"))
            extracted_text = str(exp_res.content) if exp_res.content else ""

            # Extract tables & elements
            tables_data = []
            elements_data = []

            for page in p_result.document_ir.pages:
                for block in page.blocks:
                    bbox_list = block.bbox.as_list() if hasattr(block, "bbox") and hasattr(block.bbox, "as_list") else None
                    elements_data.append({
                        "type": str(getattr(block, "type", "text")),
                        "text": str(getattr(block, "text", "")),
                        "bbox": bbox_list,
                    })

            return BenchmarkConversionResult(
                adapter_name=self.name,
                success=True,
                page_count=len(p_result.document_ir.pages),
                extracted_text=extracted_text,
                tables=tables_data,
                elements=elements_data,
                latency_sec=round(elapsed, 4),
                peak_ram_mb=round(peak_mem / (1024 * 1024), 2),
            )

        except Exception as exc:
            tracemalloc.stop()
            return BenchmarkConversionResult(
                adapter_name=self.name,
                success=False,
                error_message=str(exc),
                latency_sec=round(time.perf_counter() - t0, 4),
            )
