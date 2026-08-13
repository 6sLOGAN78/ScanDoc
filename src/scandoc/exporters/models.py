"""
Pydantic data models for export options and export results.
"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field

from scandoc.exporters.taxonomy import ImageHandlingStrategy, OutputDestination


class ExportOptions(BaseModel):
    """
    Provider-independent export configuration parameters.
    """
    format_id: str = Field("markdown", description="Target format identifier (markdown, html, json, text, docx)")
    destination: OutputDestination = Field(OutputDestination.STRING, description="Output destination type")
    output_path: Optional[str] = Field(None, description="Optional target file path if destination is FILE_PATH")
    image_strategy: ImageHandlingStrategy = Field(ImageHandlingStrategy.EMBED_BASE64, description="Image handling strategy")
    asset_dir: Optional[str] = Field(None, description="Asset directory path if image_strategy is FILE_REFERENCE")
    include_metadata: bool = Field(True, description="Include document metadata header/section")
    include_provenance: bool = Field(True, description="Include block provenance metadata")
    include_coordinates: bool = Field(False, description="Include block spatial bounding boxes")
    table_fallback_html: bool = Field(True, description="Use HTML table fallback in Markdown for merged cells")


class ExportResult(BaseModel):
    """
    Container for document exporter execution output.
    """
    format_id: str = Field(..., description="Exporter format ID")
    destination: OutputDestination = Field(..., description="Target output destination type")
    content: Union[str, bytes] = Field(..., description="Exported document string or binary bytes")
    output_path: Optional[str] = Field(None, description="Output file path if written to disk")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings emitted during export")
    asset_references: List[str] = Field(default_factory=list, description="List of resolved asset paths or identifiers")
