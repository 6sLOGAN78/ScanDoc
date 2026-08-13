"""
Unit, integration, stress, and streaming test suite for Phase 21: High-Performance Pipelines.
"""

import asyncio
import pytest

from scandoc.pipelines import (
    DocumentPipeline,
    OrderingMode,
    PipelineCancelledError,
    PipelineConfig,
    PipelineMetrics,
    PipelineResult,
    PipelineThreadPool,
    QueueOverflowError,
)


def test_single_document_pipeline_processing():
    """Test single document processing through DocumentPipeline."""
    pipeline = DocumentPipeline(config=PipelineConfig(export_format="markdown"))
    sample_text = b"Heading Title\n\nFirst paragraph text in document."

    res = pipeline.process(sample_text, file_name="sample.txt")

    assert isinstance(res, PipelineResult)
    assert res.status == "success"
    assert res.document_ir is not None
    assert res.metrics.documents_processed == 1
    assert res.exported_content is not None
    assert "Heading Title" in str(res.exported_content)


def test_batch_and_streaming_processing():
    """Test batch processing and streaming outputs in ORDERED and COMPLETION_ORDER modes."""
    config_ordered = PipelineConfig(max_workers=2, ordering_mode=OrderingMode.ORDERED)
    pipeline = DocumentPipeline(config=config_ordered)

    docs = [f"Document {i} line content.".encode("utf-8") for i in range(5)]

    # Stream in ORDERED mode
    results = list(pipeline.stream(docs))
    assert len(results) == 5
    for idx, r in enumerate(results):
        assert r.status == "success"
        assert r.document_id == f"doc_{idx}"

    # Stream in COMPLETION_ORDER mode
    pipeline.config.ordering_mode = OrderingMode.COMPLETION_ORDER
    res_completion = list(pipeline.stream(docs))
    assert len(res_completion) == 5


@pytest.mark.asyncio
async def test_async_pipeline_processing():
    """Test process_async and stream_async coroutines."""
    pipeline = DocumentPipeline()
    sample_text = b"Async document text line."

    res = await pipeline.process_async(sample_text, file_name="async_doc.txt")
    assert res.status == "success"
    assert res.document_id == "async_doc.txt"

    # Async stream test
    stream_results = []
    async for item in pipeline.stream_async([sample_text, sample_text]):
        stream_results.append(item)
    assert len(stream_results) == 2


def test_error_isolation_in_batch():
    """Test that a corrupted/failing document does not terminate other valid documents in a batch."""
    pipeline = DocumentPipeline()
    valid_doc = b"Valid document text"
    corrupted_doc = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08"

    # Ingesting corrupted binary payload returns a failed PipelineResult without throwing unhandled exception
    res_list = pipeline.process_many([valid_doc, corrupted_doc, valid_doc])

    assert len(res_list) == 3
    assert res_list[0].status == "success"
    assert res_list[1].status == "failed"
    assert res_list[2].status == "success"


def test_pipeline_cancellation_signal():
    """Test thread pool cancellation signals preventing new task submissions."""
    config = PipelineConfig(max_workers=2)
    pool = PipelineThreadPool(config)

    pool.cancel()
    assert pool.is_cancelled is True

    with pytest.raises(PipelineCancelledError):
        pool.submit_task(lambda: 42)

    pool.shutdown(wait=False)
