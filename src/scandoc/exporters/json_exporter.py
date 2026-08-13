"""
JsonExporter providing 100% loss-free DocumentIR JSON serialization and deserialization.
"""

import json
from typing import Optional, Union

from scandoc.exporters.base import BaseExporter
from scandoc.exporters.models import ExportOptions, ExportResult
from scandoc.exporters.taxonomy import OutputDestination
from scandoc.models import DocumentIR


class JsonExporter(BaseExporter):
    """
    Exporter converting DocumentIR into loss-free, deterministic JSON documents.
    """

    @property
    def format_id(self) -> str:
        return "json"

    @property
    def description(self) -> str:
        return "Loss-free JSON DocumentIR Exporter"

    def export(
        self,
        document: DocumentIR,
        options: Optional[ExportOptions] = None,
    ) -> ExportResult:
        opts = options or ExportOptions(format_id="json")

        # 100% loss-free serialization using pydantic JSON serialization
        if hasattr(document, "model_dump_json"):
            json_str = document.model_dump_json(indent=2)
        else:
            json_str = json.dumps(document.dict(), indent=2)

        output_path = opts.output_path
        if opts.destination == OutputDestination.FILE_PATH and output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_str)

        return ExportResult(
            format_id="json",
            destination=opts.destination,
            content=json_str if opts.destination != OutputDestination.BYTES else json_str.encode("utf-8"),
            output_path=output_path,
            warnings=[],
            asset_references=[],
        )

    @classmethod
    def deserialize(cls, json_payload: Union[str, bytes]) -> DocumentIR:
        """
        Deserialize JSON string or bytes back into full DocumentIR instance.
        """
        if isinstance(json_payload, bytes):
            json_payload = json_payload.decode("utf-8")

        if hasattr(DocumentIR, "model_validate_json"):
            return DocumentIR.model_validate_json(json_payload)
        return DocumentIR.parse_raw(json_payload)
