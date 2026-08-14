"""
Test suite for Phase 36: RAG Vector Embeddings & Multi-Format Exporters.
"""

import json
import zipfile
import pytest

from scandoc.exporters import (
    EpubExporter,
    ExporterRegistry,
    ExportOptions,
    PdfaExporter,
    RagChunk,
    RagExporter,
    default_exporter_registry,
)
from scandoc.models import BlockType, DocumentIR, DocumentMetadata, HeadingBlock, Page, ParagraphBlock, TextBlock
from scandoc.models.geometry import BoundingBox


@pytest.fixture
def sample_document():
    doc = DocumentIR(id="doc_123", metadata=DocumentMetadata(id="meta_123", name="test_paper.pdf", title="Sample Technical Document"))
    page = Page(page_index=0, width=612.0, height=792.0)
    
    page.blocks.append(
        HeadingBlock(
            id="b1",
            text="Section 1: Introduction",
            level=1,
            bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.15, is_normalized=True),
        )
    )
    page.blocks.append(
        ParagraphBlock(
            id="b2",
            text="This is a technical paper describing RAG vector embeddings and multi-format exporters.",
            bbox=BoundingBox(left=0.1, top=0.2, right=0.9, bottom=0.3, is_normalized=True),
        )
    )
    doc.pages.append(page)
    return doc


def test_rag_exporter_chunking_and_metadata(sample_document):
    """Test RagExporter extracting semantic chunks with metadata."""
    exporter = RagExporter(format_id="rag_json")
    res = exporter.export(sample_document)
    
    assert res.format_id == "rag_json"
    chunks_data = json.loads(res.content)
    assert len(chunks_data) == 2
    
    c0 = chunks_data[0]
    assert c0["metadata"]["chunk_type"] == "heading"
    assert c0["metadata"]["page_index"] == 0
    assert c0["metadata"]["bbox"] == [0.1, 0.1, 0.9, 0.15]


def test_rag_vector_adapters_langchain_and_llamaindex(sample_document):
    """Test RagExporter vector adapters for LangChain, LlamaIndex, Chroma, Qdrant, Pinecone."""
    # LangChain
    lc_res = default_exporter_registry.export(sample_document, options=ExportOptions(format_id="langchain"))
    lc_data = json.loads(lc_res.content)
    assert "page_content" in lc_data[0]
    assert "metadata" in lc_data[0]

    # LlamaIndex
    llama_res = default_exporter_registry.export(sample_document, options=ExportOptions(format_id="llamaindex"))
    llama_data = json.loads(llama_res.content)
    assert "text" in llama_data[0]
    assert "extra_info" in llama_data[0]

    # Chroma
    chroma_res = default_exporter_registry.export(sample_document, options=ExportOptions(format_id="chroma"))
    chroma_data = json.loads(chroma_res.content)
    assert "document" in chroma_data[0]

    # Qdrant
    qdrant_res = default_exporter_registry.export(sample_document, options=ExportOptions(format_id="qdrant"))
    qdrant_data = json.loads(qdrant_res.content)
    assert "payload" in qdrant_data[0]


def test_epub_exporter_binary_zip(sample_document):
    """Test EpubExporter generating valid EPUB zip archive."""
    exporter = EpubExporter()
    res = exporter.export(sample_document)
    
    assert res.format_id == "epub"
    assert isinstance(res.content, bytes)

    # Verify EPUB ZIP structure
    import io
    zip_buffer = io.BytesIO(res.content)
    with zipfile.ZipFile(zip_buffer, "r") as z:
        names = z.namelist()
        assert "mimetype" in names
        assert "META-INF/container.xml" in names
        assert "OEBPS/content.opf" in names
        assert "OEBPS/chapter1.xhtml" in names
        
        mimetype_bytes = z.read("mimetype")
        assert mimetype_bytes.strip() == b"application/epub+zip"


def test_pdfa_exporter_accessibility(sample_document):
    """Test PdfaExporter creating PDF/A formatted output."""
    exporter = PdfaExporter()
    res = exporter.export(sample_document)
    
    assert res.format_id == "pdfa"
    assert b"pdfa-compliance" in res.content
    assert b"Sample Technical Document" in res.content
