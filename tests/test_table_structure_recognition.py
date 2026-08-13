"""
Unit and integration test suite for Phase 11: Table Detection & Structure Recognition.
"""

from typing import BinaryIO, List, Optional, Union
import pytest

from scandoc.models import DocumentIR, DocumentMetadata, Page
from scandoc.models.blocks import TableBlock, TableCell
from scandoc.models.geometry import BoundingBox
from scandoc.models.provenance import ProcessingStage, Provenance
from scandoc.providers.ocr.models import OCRTextRegion
from scandoc.providers.tables import (
    BaseTableProvider,
    OcrToCellMapper,
    SlaNetTableProvider,
    TableCellStructure,
    TableColumnStructure,
    TableRowStructure,
    TableProviderRegistry,
    TableStructureConfig,
    TableStructureResult,
    table_structure_to_document_ir,
    TableProviderUnavailableError,
)


class MockTableProvider(BaseTableProvider):
    """Mock table structure provider for deterministic unit testing without external weights."""

    @property
    def provider_id(self) -> str:
        return "mock_table_provider"

    @property
    def model_id(self) -> str:
        return "Mock-SLANet-v1"

    def initialize(self, config: Optional[TableStructureConfig] = None) -> None:
        pass

    def infer_table_structure(
        self,
        image_input: Union[str, bytes, bytearray, BinaryIO],
        table_bbox: Optional[BoundingBox] = None,
        page_index: int = 0,
        config: Optional[TableStructureConfig] = None,
    ) -> TableStructureResult:
        tb_bbox = table_bbox or BoundingBox(left=0.1, top=0.2, right=0.9, bottom=0.8, is_normalized=True)

        prov = Provenance(provider=self.provider_id, model=self.model_id, stage=ProcessingStage.TABLE_RECOGNITION)

        # Create 2x2 grid with merged cell in row 0
        cells = [
            TableCellStructure(
                cell_id="c0_0",
                row_index=0,
                col_index=0,
                row_span=1,
                col_span=2,
                bbox=BoundingBox(left=0.1, top=0.2, right=0.9, bottom=0.5, is_normalized=True),
                text="Merged Header A+B",
                is_header=True,
                provenance=prov,
            ),
            TableCellStructure(
                cell_id="c1_0",
                row_index=1,
                col_index=0,
                row_span=1,
                col_span=1,
                bbox=BoundingBox(left=0.1, top=0.5, right=0.5, bottom=0.8, is_normalized=True),
                text="Val 1",
                is_header=False,
                provenance=prov,
            ),
            TableCellStructure(
                cell_id="c1_1",
                row_index=1,
                col_index=1,
                row_span=1,
                col_span=1,
                bbox=BoundingBox(left=0.5, top=0.5, right=0.9, bottom=0.8, is_normalized=True),
                text="Val 2",
                is_header=False,
                provenance=prov,
            ),
        ]

        return TableStructureResult(
            table_id="table_mock_1",
            page_index=page_index,
            bbox=tb_bbox,
            num_rows=2,
            num_cols=2,
            rows=[TableRowStructure(row_index=0, is_header=True), TableRowStructure(row_index=1, is_header=False)],
            cols=[TableColumnStructure(col_index=0), TableColumnStructure(col_index=1)],
            cells=cells,
            confidence=0.99,
            provider_id=self.provider_id,
            model_id=self.model_id,
            processing_time_ms=8.5,
            provenance=prov,
        )


def test_table_structure_result_validation():
    """Test TableStructureResult and TableCellStructure schema validation."""
    bbox = BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.9, is_normalized=True)
    cell = TableCellStructure(
        cell_id="c1",
        row_index=0,
        col_index=0,
        row_span=2,
        col_span=1,
        bbox=bbox,
        confidence=0.95,
    )
    assert cell.row_span == 2
    assert cell.col_span == 1

    res = TableStructureResult(
        table_id="t1",
        page_index=0,
        bbox=bbox,
        num_rows=2,
        num_cols=2,
        cells=[cell],
        provider_id="test_p",
        model_id="test_m",
    )
    assert res.num_rows == 2
    assert len(res.cells) == 1


def test_ocr_to_cell_mapping():
    """Test OcrToCellMapper mapping OCR text regions into table grid cells using bounding box overlap."""
    cell1 = TableCellStructure(
        cell_id="c1",
        row_index=0,
        col_index=0,
        bbox=BoundingBox(left=0.0, top=0.0, right=0.5, bottom=0.5, is_normalized=True),
    )
    cell2 = TableCellStructure(
        cell_id="c2",
        row_index=0,
        col_index=1,
        bbox=BoundingBox(left=0.5, top=0.0, right=1.0, bottom=0.5, is_normalized=True),
    )

    ocr_regions = [
        OCRTextRegion(
            text="Cell One Data",
            bbox=BoundingBox(left=0.05, top=0.05, right=0.4, bottom=0.4, is_normalized=True),
            confidence=0.99,
        ),
        OCRTextRegion(
            text="Cell Two Data",
            bbox=BoundingBox(left=0.55, top=0.05, right=0.9, bottom=0.4, is_normalized=True),
            confidence=0.98,
        ),
    ]

    mapped_cells = OcrToCellMapper.map_text_to_cells([cell1, cell2], ocr_regions)
    c1_mapped = next(c for c in mapped_cells if c.cell_id == "c1")
    c2_mapped = next(c for c in mapped_cells if c.cell_id == "c2")

    assert c1_mapped.text == "Cell One Data"
    assert c2_mapped.text == "Cell Two Data"


def test_table_structure_to_document_ir_conversion():
    """Test converting TableStructureResult into DocumentIR TableBlock and TableCell IR models."""
    mock_p = MockTableProvider()
    t_res = mock_p.infer_table_structure(b"fake_image_bytes", page_index=0)

    tb_block: TableBlock = table_structure_to_document_ir(t_res)

    assert isinstance(tb_block, TableBlock)
    assert tb_block.num_rows == 2
    assert tb_block.num_cols == 2
    assert len(tb_block.cells) == 3

    c0 = tb_block.cells[0]
    assert c0.row_span == 1
    assert c0.col_span == 2
    assert c0.is_header is True
    assert c0.text == "Merged Header A+B"

    assert tb_block.provenance.provider == "mock_table_provider"
    assert tb_block.provenance.stage == ProcessingStage.TABLE_RECOGNITION


def test_slanet_provider_availability():
    """Test SlaNetTableProvider capability and graceful missing model handling."""
    prov = SlaNetTableProvider(config=TableStructureConfig(model_path="/non_existent/slanet.onnx"))
    assert prov.provider_id == "slanet_table"
    assert prov.is_available is False

    with pytest.raises(TableProviderUnavailableError):
        prov.initialize()


def test_table_provider_registry():
    """Test TableProviderRegistry lifecycle."""
    registry = TableProviderRegistry(register_defaults=False)
    mock_p = MockTableProvider()
    registry.register(mock_p)

    assert len(registry.list_providers()) == 1
    assert registry.get_provider("mock_table_provider").provider_id == "mock_table_provider"
    assert registry.select_provider().provider_id == "mock_table_provider"
