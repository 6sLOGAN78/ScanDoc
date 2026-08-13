"""
Unit and integration test suite for Phase 18: Multi-Format Document Ingestion & Normalization.
"""

import io
from pathlib import Path
import tempfile
import pytest

from scandoc.ingestion import (
    AssetRef,
    CorruptedDocumentError,
    DocumentIngestor,
    IngestionOptions,
    InvalidFileError,
    OversizedInputError,
    SourceDataType,
    UnsupportedFormatError,
)
from scandoc.models import DocumentIR


def test_document_ingestor_bytes_payload():
    """Test DocumentIngestor ingesting text bytes payload into DocumentIR."""
    ingestor = DocumentIngestor()
    content = b"# Document Title\n\nSample paragraph text for multi-format ingestion test."

    doc_ir = ingestor.ingest(content, file_name="sample.md")
    assert isinstance(doc_ir, DocumentIR)
    assert doc_ir.metadata.page_count >= 1
    assert len(doc_ir.pages) >= 1
    assert len(doc_ir.pages[0].blocks) >= 1


def test_document_ingestor_stream():
    """Test DocumentIngestor ingesting from io.BytesIO stream."""
    ingestor = DocumentIngestor()
    stream = io.BytesIO(b"Plain text stream payload content")

    doc_ir = ingestor.ingest(stream, file_name="test.txt")
    assert isinstance(doc_ir, DocumentIR)
    assert len(doc_ir.pages[0].blocks) >= 1


def test_document_ingestor_oversized_file():
    """Test DocumentIngestor enforcing maximum file size limits."""
    opts = IngestionOptions(max_file_size_bytes=50)
    ingestor = DocumentIngestor(options=opts)
    big_payload = b"A" * 100

    with pytest.raises(OversizedInputError):
        ingestor.ingest(big_payload, file_name="big.txt")


def test_document_ingestor_missing_file():
    """Test DocumentIngestor raising InvalidFileError for non-existent file paths."""
    ingestor = DocumentIngestor()

    with pytest.raises(InvalidFileError):
        ingestor.ingest("/non_existent_directory/missing_file.pdf")


def test_format_detection_bypasses_misleading_extension():
    """Security Test: FormatDetector must rely on magic bytes rather than misleading extensions."""
    ingestor = DocumentIngestor()
    # TXT content in a file named "fake.pdf"
    fake_pdf = b"Plain text content inside a file named fake.pdf"

    # Should detect as TXT and ingest successfully
    doc_ir = ingestor.ingest(fake_pdf, file_name="fake.pdf")
    assert isinstance(doc_ir, DocumentIR)
    assert len(doc_ir.pages) == 1
