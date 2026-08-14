"""
Comprehensive test suite for Phase 30: Real Table Structure Recognition & Deep-Learning Integration.
"""

import io
from pathlib import Path
import tempfile
from PIL import Image, ImageDraw
import pytest

from scandoc.exporters import HtmlExporter, MarkdownExporter
from scandoc.models import DocumentIR
from scandoc.models.blocks import TableBlock, TextBlock
from scandoc.models.geometry import BoundingBox
from scandoc.models_mgmt import default_model_manager
from scandoc.models_mgmt.taxonomy import TaskType
from scandoc.providers.ocr.models import OCRTextRegion
from scandoc.providers.tables import (
    OcrToCellMapper,
    SlaNetTableProvider,
    TableCellStructure,
    TableStructureConfig,
    TableStructureResult,
    table_structure_to_document_ir,
)
from scandoc.models.provenance import ProcessingStage


@pytest.fixture
def slanet_provider():
    prov = SlaNetTableProvider()
    if not prov.is_available:
        pytest.skip("onnxruntime dependency not installed.")
    return prov


@pytest.fixture
def table_crop_image_bytes():
    """Generate a clean synthetic table grid image."""
    img = Image.new("RGB", (600, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Outer border
    draw.rectangle([10, 10, 590, 390], outline=(0, 0, 0), width=2)
    # Header divider
    draw.line([10, 100, 590, 100], fill=(0, 0, 0), width=2)
    # Column divider
    draw.line([300, 10, 300, 390], fill=(0, 0, 0), width=2)

    draw.text((30, 40), "Header Column A", fill=(0, 0, 0))
    draw.text((320, 40), "Header Column B", fill=(0, 0, 0))
    draw.text((30, 200), "Row 1 Data A", fill=(0, 0, 0))
    draw.text((320, 200), "Row 1 Data B", fill=(0, 0, 0))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# 1. SLANet Provider Capability & Availability Test
def test_slanet_table_provider_initialization(slanet_provider):
    """Verify SLANet Table Provider initialization and provider metadata."""
    assert slanet_provider.provider_id == "slanet_table"
    assert "SLANet" in slanet_provider.model_id


# 2. Real Table Structure Inference Test
def test_slanet_real_table_structure_inference(slanet_provider, table_crop_image_bytes):
    """Verify table structure inference produces structured cells with row/column indices."""
    tb_bbox = BoundingBox(left=0.1, top=0.2, right=0.9, bottom=0.8, is_normalized=True)
    result: TableStructureResult = slanet_provider.infer_table_structure(
        table_crop_image_bytes, table_bbox=tb_bbox, page_index=0
    )

    assert result is not None
    assert result.provider_id == "slanet_table"
    assert result.num_rows >= 1
    assert result.num_cols >= 1
    assert len(result.cells) == result.num_rows * result.num_cols

    for cell in result.cells:
        assert cell.row_index >= 0
        assert cell.col_index >= 0
        assert cell.row_span >= 1
        assert cell.col_span >= 1
        assert 0.0 <= cell.bbox.left <= 1.0
        assert 0.0 <= cell.bbox.top <= 1.0


# 3. OCR / Native Text to Cell Spatial Association Test
def test_ocr_to_cell_text_association():
    """Verify OcrToCellMapper maps text spans to table cells based on geometric overlap."""
    cells = [
        TableCellStructure(
            cell_id="c0_0",
            row_index=0,
            col_index=0,
            bbox=BoundingBox(left=0.1, top=0.2, right=0.5, bottom=0.5, is_normalized=True),
        ),
        TableCellStructure(
            cell_id="c0_1",
            row_index=0,
            col_index=1,
            bbox=BoundingBox(left=0.5, top=0.2, right=0.9, bottom=0.5, is_normalized=True),
        ),
    ]

    text_spans = [
        OCRTextRegion(
            text="Name",
            bbox=BoundingBox(left=0.15, top=0.25, right=0.45, bottom=0.45, is_normalized=True),
            confidence=0.95,
        ),
        OCRTextRegion(
            text="Salary",
            bbox=BoundingBox(left=0.55, top=0.25, right=0.85, bottom=0.45, is_normalized=True),
            confidence=0.95,
        ),
    ]

    mapped_cells = OcrToCellMapper.map_text_to_cells(cells, text_spans)

    assert mapped_cells[0].text == "Name"
    assert mapped_cells[1].text == "Salary"


# 4. Table Structure to DocumentIR TableBlock Conversion Test
def test_table_structure_to_document_ir(slanet_provider, table_crop_image_bytes):
    """Verify TableStructureResult maps into DocumentIR TableBlock and TableCell models."""
    result = slanet_provider.infer_table_structure(table_crop_image_bytes, page_index=0)
    table_block: TableBlock = table_structure_to_document_ir(result)

    assert table_block is not None
    assert table_block.num_rows == result.num_rows
    assert table_block.num_cols == result.num_cols
    assert len(table_block.cells) == len(result.cells)
    assert table_block.provenance is not None
    assert table_block.provenance.provider == "slanet_table"
    assert table_block.provenance.stage == ProcessingStage.TABLE_RECOGNITION


# 5. Table Exporting to HTML and Markdown Test
def test_table_export_to_html_and_markdown(slanet_provider, table_crop_image_bytes):
    """Verify TableBlock exports to HTML table structure and Markdown table matrix."""
    result = slanet_provider.infer_table_structure(table_crop_image_bytes, page_index=0)
    table_block = table_structure_to_document_ir(result)

    # Populate cell text for test assertion
    if table_block.cells:
        table_block.cells[0].text = "Header A"
        if len(table_block.cells) > 1:
            table_block.cells[1].text = "Header B"

    from scandoc.models import DocumentMetadata, Page
    doc_ir = DocumentIR(
        metadata=DocumentMetadata(id="test_doc", name="Test Document"),
        pages=[Page(page_index=0, page_number=1, width=600, height=400, blocks=[table_block])],
    )

    html_exporter = HtmlExporter()
    html_out = html_exporter.export(doc_ir)
    assert "<table" in html_out.content
    assert "Header A" in html_out.content

    md_exporter = MarkdownExporter()
    md_out = md_exporter.export(doc_ir)
    assert "|" in md_out.content


# 6. ModelManager Spec Lifecycle Test for slanet_table
def test_model_manager_slanet_spec_lifecycle():
    """Verify slanet_table is registered in ModelRegistry for TaskType.TABLE."""
    mgr = default_model_manager
    models = mgr.list_available_models(task=TaskType.TABLE)

    table_ids = [m.model_id for m in models]
    assert "slanet_table" in table_ids
