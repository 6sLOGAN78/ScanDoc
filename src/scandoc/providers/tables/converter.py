"""
Converter mapping TableStructureResult into DocumentIR TableBlock and TableCell IR models.
"""

from typing import List, Optional

from scandoc.models.blocks import TableBlock, TableCell
from scandoc.models.provenance import ProcessingStage, Provenance
from scandoc.providers.tables.models import TableStructureResult


def table_structure_to_document_ir(
    table_struct: TableStructureResult,
    target_table_block: Optional[TableBlock] = None,
) -> TableBlock:
    """
    Convert TableStructureResult into DocumentIR TableBlock and TableCell models.
    
    Preserves row_span, col_span, cell coordinates, header classification, and provenance.
    Does NOT flatten merged cells.
    """
    prov = Provenance(
        provider=table_struct.provider_id,
        model=table_struct.model_id,
        stage=ProcessingStage.TABLE_RECOGNITION,
        confidence=table_struct.confidence,
    )

    ir_cells: List[TableCell] = []
    for cell in table_struct.cells:
        ir_cell = TableCell(
            cell_id=cell.cell_id,
            row_index=cell.row_index,
            col_index=cell.col_index,
            row_span=cell.row_span,
            col_span=cell.col_span,
            text=cell.text,
            bbox=cell.bbox,
            is_header=cell.is_header,
        )
        ir_cells.append(ir_cell)

    if target_table_block is not None:
        target_table_block.num_rows = table_struct.num_rows
        target_table_block.num_cols = table_struct.num_cols
        target_table_block.cells = ir_cells
        target_table_block.bbox = table_struct.bbox
        target_table_block.provenance = prov
        return target_table_block

    return TableBlock(
        id=table_struct.table_id,
        num_rows=table_struct.num_rows,
        num_cols=table_struct.num_cols,
        cells=ir_cells,
        bbox=table_struct.bbox,
        provenance=prov,
    )
