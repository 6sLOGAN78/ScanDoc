"""
DocumentPipeline central entry point for batching, streaming, worker pools, and async execution.
"""

import asyncio
from concurrent.futures import as_completed
import logging
import time
from typing import AsyncGenerator, Generator, List, Optional, Union

from scandoc.agent.document_agent import DocumentAgent
from scandoc.analysis.layout_analyzer import LayoutAnalyzer
from scandoc.exporters.registry import ExporterRegistry, default_exporter_registry
from scandoc.ingestion.ingestor import DocumentIngestor
from scandoc.models import DocumentIR
from scandoc.pipelines.executor import PipelineThreadPool
from scandoc.pipelines.models import PipelineConfig, PipelineMetrics, PipelineResult
from scandoc.pipelines.taxonomy import OrderingMode

logger = logging.getLogger("scandoc.pipelines.pipeline")


class DocumentPipeline:
    """
    High-Performance Document Processing Pipeline.
    Supports single document processing, batch worker pools, streaming generators, and async coroutines.
    """

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        ingestor: Optional[DocumentIngestor] = None,
        agent: Optional[DocumentAgent] = None,
        exporter_registry: Optional[ExporterRegistry] = None,
    ):
        self.config = config or PipelineConfig()
        self.ingestor = ingestor or DocumentIngestor()
        self.agent = agent or DocumentAgent()
        self.exporter_registry = exporter_registry or default_exporter_registry

    def process(
        self,
        source: Union[str, bytes],
        file_name: Optional[str] = None,
    ) -> PipelineResult:
        """
        Process single document source synchronously.
        """
        start_time = time.perf_counter()
        doc_id = file_name or "doc_single"
        errors: List[str] = []

        try:
            # 1. Ingestion Stage
            doc_ir = self.ingestor.ingest(source, file_name=file_name)
            doc_id = doc_ir.metadata.name or doc_id

            # 2. Agentic Routing / Plan Stage
            plan = self.agent.plan(source)

            # 3. Layout & Structure Analysis Stage
            for page in doc_ir.pages:
                LayoutAnalyzer.analyze_page(page, page_width=page.width, page_height=page.height)

            # 4. Optional Exporter Stage
            exported_content = None
            if self.config.export_format:
                from scandoc.exporters.models import ExportOptions
                exp_opts = ExportOptions(format_id=self.config.export_format)
                exp_res = self.exporter_registry.export(doc_ir, options=exp_opts)
                exported_content = exp_res.content
                if exp_res.warnings:
                    errors.extend(exp_res.warnings)

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            page_cnt = len(doc_ir.pages)
            pages_per_sec = (page_cnt / (elapsed_ms / 1000.0)) if elapsed_ms > 0 else 0.0

            metrics = PipelineMetrics(
                documents_processed=1,
                pages_processed=page_cnt,
                successful_pages=page_cnt,
                failed_pages=0,
                total_processing_time_ms=elapsed_ms,
                average_page_latency_ms=elapsed_ms / page_cnt if page_cnt > 0 else 0.0,
                pages_per_second=pages_per_sec,
            )

            return PipelineResult(
                document_id=doc_id,
                document_ir=doc_ir,
                status="success",
                errors=errors,
                metrics=metrics,
                exported_content=exported_content,
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error("Document processing failed for '%s': %s", doc_id, e)
            return PipelineResult(
                document_id=doc_id,
                document_ir=None,
                status="failed",
                errors=[str(e)],
                metrics=PipelineMetrics(total_processing_time_ms=elapsed_ms),
                exported_content=None,
            )

    def process_many(
        self,
        sources: List[Union[str, bytes]],
    ) -> List[PipelineResult]:
        """
        Process multiple documents concurrently using worker pool.
        """
        return list(self.stream(sources))

    def stream(
        self,
        sources: List[Union[str, bytes]],
    ) -> Generator[PipelineResult, None, None]:
        """
        Stream PipelineResult items incrementally as completed.
        Respects config.ordering_mode (ORDERED vs COMPLETION_ORDER).
        """
        pool = PipelineThreadPool(self.config)
        futures = []

        try:
            for idx, src in enumerate(sources):
                file_name = f"doc_{idx}" if isinstance(src, bytes) else str(src)
                fut = pool.submit_task(self.process, src, file_name=file_name)
                futures.append((idx, fut))

            if self.config.ordering_mode == OrderingMode.COMPLETION_ORDER:
                # Completion Order Mode: Yield as completed
                future_map = {f: idx for idx, f in futures}
                for completed_fut in as_completed(future_map.keys()):
                    yield completed_fut.result()
            else:
                # Ordered Mode: Yield in strict input sequence order
                for idx, fut in futures:
                    yield fut.result()

        finally:
            pool.shutdown(wait=True)

    async def process_async(
        self,
        source: Union[str, bytes],
        file_name: Optional[str] = None,
    ) -> PipelineResult:
        """
        Asynchronous coroutine wrapper for single document processing.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.process, source, file_name)

    async def stream_async(
        self,
        sources: List[Union[str, bytes]],
    ) -> AsyncGenerator[PipelineResult, None]:
        """
        Asynchronous generator streaming PipelineResult items.
        """
        for res in self.stream(sources):
            yield res
            await asyncio.sleep(0)
