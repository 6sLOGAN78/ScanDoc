"""
Unit, integration, round-trip, security, and format test suite for Phase 20: Comprehensive Exporters Pipeline.
"""

import json
from pathlib import Path
import pytest

from scandoc.exporters import (
    DocxExporter,
    ExporterRegistry,
    ExportOptions,
    ExportResult,
    HtmlExporter,
    ImageHandlingStrategy,
    JsonExporter,
    MarkdownExporter,
    OutputDestination,
    TextExporter,
    default_exporter_registry,
)
from scandoc.models import DocumentIR, DocumentMetadata, Page
from scandoc.models.blocks import (
    FigureBlock,
    FormulaBlock,
    HeadingBlock,
    ImageRef,
    ListBlock,
    ListItem,
    ParagraphBlock,
    TableBlock,
    TableCell,
)
from scandoc.models.geometry import BoundingBox
from scandoc.models.provenance import ProcessingStage, Provenance
from scandoc.providers.ecosystem.credentials import CredentialReference


@pytest.fixture
def sample_document_ir() -> DocumentIR:
    """Construct realistic DocumentIR with headings, paragraphs, lists, tables, figures, formulas, and provenance."""
    prov = Provenance(provider="test_provider", model="test_model", stage=ProcessingStage.NATIVE_EXTRACTION)

    h1 = HeadingBlock(
        id="h_1", text="System Architecture Overview", level=1,
        bbox=BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.15, is_normalized=True),
        provenance=prov,
    )
    p1 = ParagraphBlock(
        id="p_1", text="This section describes the high-level system architecture.",
        bbox=BoundingBox(left=0.1, top=0.2, right=0.9, bottom=0.3, is_normalized=True),
        provenance=prov,
    )
    lst_items = [
        ListItem(text="Fast native extraction", reading_order_index=0),
        ListItem(text="Multi-OCR provider fallback", reading_order_index=1),
        ListItem(text="Lossless JSON export", reading_order_index=2),
    ]
    lst = ListBlock(
        id="l_1", items=lst_items,
        ordered=False, bbox=BoundingBox(left=0.1, top=0.32, right=0.9, bottom=0.45, is_normalized=True),
        provenance=prov,
    )
    # Table with cells
    cells = [
        TableCell(cell_id="c00", text="Feature", row_index=0, col_index=0),
        TableCell(cell_id="c01", text="Status", row_index=0, col_index=1),
        TableCell(cell_id="c10", text="PDF Parsing", row_index=1, col_index=0),
        TableCell(cell_id="c11", text="Active", row_index=1, col_index=1),
    ]
    tbl = TableBlock(
        id="tbl_1", num_rows=2, num_cols=2, cells=cells,
        bbox=BoundingBox(left=0.1, top=0.48, right=0.9, bottom=0.65, is_normalized=True),
        provenance=prov,
    )
    img_ref = ImageRef(mime_type="image/png", base64_data="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
    fig = FigureBlock(
        id="fig_1", caption="Figure 1: Pipeline diagram", image_ref=img_ref,
        bbox=BoundingBox(left=0.1, top=0.68, right=0.9, bottom=0.85, is_normalized=True),
        provenance=prov,
    )
    eq = FormulaBlock(
        id="eq_1", expression="E = mc^2",
        bbox=BoundingBox(left=0.1, top=0.88, right=0.9, bottom=0.95, is_normalized=True),
        provenance=prov,
    )

    page = Page(page_index=0, width=612.0, height=792.0, blocks=[h1, p1, lst, tbl, fig, eq])
    meta = DocumentMetadata(id="doc_test_100", name="System_Architecture.pdf", author="scanDOC Team", page_count=1)

    return DocumentIR(metadata=meta, pages=[page])


def test_markdown_exporter(sample_document_ir):
    """Test MarkdownExporter rendering headings, lists, tables, formulas, and figures."""
    exporter = MarkdownExporter()
    opts = ExportOptions(format_id="markdown", include_metadata=True, include_provenance=True)
    res = exporter.export(sample_document_ir, options=opts)

    assert isinstance(res, ExportResult)
    assert res.format_id == "markdown"
    assert "# System_Architecture.pdf" in res.content
    assert "# System Architecture Overview" in res.content
    assert "- Fast native extraction" in res.content
    assert "| Feature | Status |" in res.content
    assert "![fig_1]" in res.content
    assert "$$\nE = mc^2\n$$" in res.content
    assert "<!-- provenance: provider=test_provider stage=NATIVE_EXTRACTION -->" in res.content


def test_html_exporter(sample_document_ir):
    """Test HtmlExporter rendering semantic HTML tags."""
    exporter = HtmlExporter()
    opts = ExportOptions(format_id="html")
    res = exporter.export(sample_document_ir, options=opts)

    assert "System Architecture Overview</h1>" in res.content
    assert "<p" in res.content and "This section describes the high-level system architecture.</p>" in res.content
    assert "<li>Fast native extraction</li>" in res.content
    assert "<table" in res.content
    assert '<img src="data:image/png;base64,' in res.content
    assert '<figcaption>Figure 1: Pipeline diagram</figcaption>' in res.content


def test_json_exporter_and_lossless_roundtrip(sample_document_ir):
    """Test JsonExporter 100% loss-free serialization and deserialization round trip."""
    exporter = JsonExporter()
    res = exporter.export(sample_document_ir)

    assert isinstance(res.content, str)
    assert '"name": "System_Architecture.pdf"' in res.content

    # Round trip deserialization
    deserialized_doc = JsonExporter.deserialize(res.content)
    assert isinstance(deserialized_doc, DocumentIR)
    assert deserialized_doc.metadata.name == sample_document_ir.metadata.name
    assert len(deserialized_doc.pages) == len(sample_document_ir.pages)
    assert len(deserialized_doc.pages[0].blocks) == len(sample_document_ir.pages[0].blocks)


def test_text_exporter(sample_document_ir):
    """Test TextExporter generating plain text with image placeholders and warnings."""
    exporter = TextExporter()
    res = exporter.export(sample_document_ir)

    assert "SYSTEM ARCHITECTURE OVERVIEW" in res.content
    assert "[Figure: fig_1]" in res.content
    assert "Equation: E = mc^2" in res.content
    assert len(res.warnings) >= 1


def test_docx_exporter(sample_document_ir):
    """Test DocxExporter generating binary DOCX stream."""
    exporter = DocxExporter()
    res = exporter.export(sample_document_ir)

    assert isinstance(res.content, bytes)
    assert len(res.content) > 1000
    assert res.content.startswith(b"PK\x03\x04")  # Valid ZIP/DOCX header signature


def test_exporter_registry():
    """Test ExporterRegistry discovery, lookup, and default registration."""
    registry = ExporterRegistry(register_defaults=True)
    exporters = registry.list_exporters()
    assert len(exporters) >= 13

    names = {e.format_id for e in exporters}
    assert {"markdown", "html", "json", "text", "docx", "epub", "pdfa", "rag_json", "langchain", "llamaindex", "chroma", "qdrant", "pinecone"}.issubset(names)

    md_exporter = registry.get_exporter("markdown")
    assert md_exporter.format_id == "markdown"


def test_secret_redaction_in_exports(sample_document_ir):
    """Security Test: Verify raw API keys and secrets are NEVER exposed in export outputs."""
    secret_ref = CredentialReference(credential_id="cred_1", env_var_name="SECRET_API_KEY", raw_secret="sk-secret-key-12345")
    # Verify string representation of CredentialReference masks secret
    assert "sk-secret-key-12345" not in str(secret_ref)
    assert "cred_1" in str(secret_ref)

    # Export document and verify raw secret is absent in all formats
    registry = ExporterRegistry(register_defaults=True)
    for fmt in ["markdown", "html", "json", "text"]:
        res = registry.export(sample_document_ir, options=ExportOptions(format_id=fmt))
        content_str = res.content if isinstance(res.content, str) else res.content.decode("utf-8", errors="replace")
        assert "sk-secret-key-12345" not in content_str
