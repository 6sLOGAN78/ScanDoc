"""
Multi-Format Document Ingestion & Normalization Subsystem for scanDOC.
"""

from scandoc.ingestion.exceptions import (
    CorruptedDocumentError,
    DependencyUnavailableError,
    IngestionError,
    InvalidFileError,
    OversizedInputError,
    ParserError,
    UnsupportedFormatError,
)
from scandoc.ingestion.ingestor import DocumentIngestor
from scandoc.ingestion.models import AssetRef, IngestionOptions
from scandoc.ingestion.taxonomy import SourceDataType

__all__ = [
    "DocumentIngestor",
    "IngestionOptions",
    "AssetRef",
    "SourceDataType",
    "IngestionError",
    "UnsupportedFormatError",
    "InvalidFileError",
    "CorruptedDocumentError",
    "ParserError",
    "DependencyUnavailableError",
    "OversizedInputError",
]
