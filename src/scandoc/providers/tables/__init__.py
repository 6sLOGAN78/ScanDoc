"""
Table Detection & Structure Recognition Subsystem for scanDOC.
"""

from scandoc.providers.tables.base import BaseTableProvider
from scandoc.providers.tables.converter import table_structure_to_document_ir
from scandoc.providers.tables.exceptions import (
    TableError,
    TableInferenceError,
    TableInitializationError,
    TableProviderUnavailableError,
)
from scandoc.providers.tables.mapper import OcrToCellMapper
from scandoc.providers.tables.models import (
    TableCellStructure,
    TableColumnStructure,
    TableRowStructure,
    TableStructureConfig,
    TableStructureResult,
)
from scandoc.providers.tables.registry import (
    TableProviderRegistry,
    default_table_registry,
)
from scandoc.providers.tables.slanet_provider import SlaNetTableProvider

__all__ = [
    "BaseTableProvider",
    "SlaNetTableProvider",
    "TableProviderRegistry",
    "default_table_registry",
    "TableStructureConfig",
    "TableCellStructure",
    "TableRowStructure",
    "TableColumnStructure",
    "TableStructureResult",
    "OcrToCellMapper",
    "table_structure_to_document_ir",
    "TableError",
    "TableProviderUnavailableError",
    "TableInitializationError",
    "TableInferenceError",
]
