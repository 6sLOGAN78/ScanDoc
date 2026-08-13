"""
DocumentIngestor orchestrating unified multi-format ingestion into normalized DocumentIR.
"""

import io
import logging
from pathlib import Path
from typing import BinaryIO, Optional, Union

from scandoc.formats.detector import FormatDetector
from scandoc.formats.exceptions import FormatError, UnsupportedFormatError as FmtUnsupportedError
from scandoc.formats.registry import FormatRegistry, default_registry
from scandoc.ingestion.exceptions import (
    CorruptedDocumentError,
    IngestionError,
    InvalidFileError,
    OversizedInputError,
    ParserError,
    UnsupportedFormatError,
)
from scandoc.ingestion.models import IngestionOptions
from scandoc.models.document import DocumentIR

logger = logging.getLogger("scandoc.ingestion.ingestor")


class DocumentIngestor:
    """
    Unified entry point for multi-format document ingestion into normalized DocumentIR.
    Enforces format detection security, size constraints, and error normalization.
    """

    def __init__(
        self,
        registry: Optional[FormatRegistry] = None,
        options: Optional[IngestionOptions] = None,
    ):
        self._registry = registry or default_registry
        self._options = options or IngestionOptions()

    def ingest(
        self,
        source: Union[str, Path, bytes, BinaryIO],
        file_name: Optional[str] = None,
        options: Optional[IngestionOptions] = None,
    ) -> DocumentIR:
        """
        Ingest input document source and return normalized DocumentIR.
        
        Args:
            source: Path, bytes payload, or binary file stream.
            file_name: Optional filename hint.
            options: Optional override IngestionOptions.
            
        Returns:
            DocumentIR instance with native document structure and provenance.
        """
        opts = options or self._options

        # 1. Validate Input Source & Size Constraints
        raw_bytes: Optional[bytes] = None
        file_path: Optional[str] = None

        if isinstance(source, (str, Path)):
            path_obj = Path(source)
            if not path_obj.exists():
                raise InvalidFileError(f"Input file not found: '{source}'")
            size = path_obj.stat().st_size
            if size > opts.max_file_size_bytes:
                raise OversizedInputError(
                    f"File size ({size} bytes) exceeds max limit ({opts.max_file_size_bytes} bytes)."
                )
            file_path = str(path_obj.resolve())

        elif isinstance(source, bytes):
            if len(source) > opts.max_file_size_bytes:
                raise OversizedInputError(
                    f"Bytes payload size ({len(source)} bytes) exceeds max limit ({opts.max_file_size_bytes} bytes)."
                )
            raw_bytes = source

        elif hasattr(source, "read"):
            buf = source.read()
            if isinstance(buf, str):
                buf = buf.encode(opts.fallback_encoding)
            if len(buf) > opts.max_file_size_bytes:
                raise OversizedInputError(
                    f"Stream payload size ({len(buf)} bytes) exceeds max limit ({opts.max_file_size_bytes} bytes)."
                )
            raw_bytes = buf
        else:
            raise InvalidFileError(f"Unsupported input source type: '{type(source).__name__}'")

        # 2. Execute Format Parsing & Detection via Registry
        try:
            parse_target = raw_bytes if raw_bytes is not None else file_path
            doc_ir = self._registry.parse(parse_target, file_path=file_name or file_path)
            return doc_ir
        except FmtUnsupportedError as e:
            raise UnsupportedFormatError(str(e)) from e
        except FormatError as e:
            raise ParserError(f"Format handler failed during parsing: {e}") from e
        except Exception as e:
            logger.error("Corrupted or invalid document during ingestion: %s", e)
            raise CorruptedDocumentError(f"Failed to parse document payload: {e}") from e
