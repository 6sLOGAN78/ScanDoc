"""
RAG Vector Embeddings Exporter producing semantic chunks for LangChain, LlamaIndex, Chroma, Qdrant, and Pinecone.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
import uuid

from pydantic import BaseModel, Field

from scandoc.exporters.base import BaseExporter
from scandoc.exporters.models import ExportOptions, ExportResult
from scandoc.exporters.taxonomy import OutputDestination
from scandoc.models import BlockType, DocumentIR, TextBlock

logger = logging.getLogger("scandoc.exporters.rag")


class RagChunkMetadata(BaseModel):
    """Metadata schema for a RAG chunk."""
    document_id: str
    document_name: str
    page_index: int
    chunk_type: str
    bbox: Optional[List[float]] = None
    heading_hierarchy: List[str] = Field(default_factory=list)
    figure_caption: Optional[str] = None
    formula_latex: Optional[str] = None
    table_matrix: Optional[List[List[str]]] = None


class RagChunk(BaseModel):
    """Semantic RAG document chunk with content and spatial/structural metadata."""
    chunk_id: str
    text: str
    metadata: RagChunkMetadata


class RagExporter(BaseExporter):
    """
    RAG Chunking and Vector Index Exporter.
    Supported format IDs: 'rag_json', 'langchain', 'llamaindex', 'chroma', 'qdrant', 'pinecone'.
    """

    def __init__(self, format_id: str = "rag_json"):
        self._format_id = format_id.lower()

    @property
    def format_id(self) -> str:
        return self._format_id

    @property
    def description(self) -> str:
        return f"RAG vector embedding exporter format '{self._format_id}'"

    @property
    def file_extension(self) -> str:
        return "json"

    def export(
        self,
        document: DocumentIR,
        options: Optional[ExportOptions] = None,
    ) -> ExportResult:
        opts = options or ExportOptions(format_id=self.format_id)
        fmt = opts.format_id.lower()

        # Step 1: Build semantic chunks
        chunks = self.extract_chunks(document)

        # Step 2: Format chunks into target vector ecosystem schema
        if fmt == "langchain":
            formatted_data = self.to_langchain(chunks)
        elif fmt == "llamaindex":
            formatted_data = self.to_llamaindex(chunks)
        elif fmt in ("chroma", "qdrant", "pinecone"):
            formatted_data = self.to_vector_records(chunks, fmt)
        else:
            # Default rag_json schema
            formatted_data = [c.model_dump() for c in chunks]

        output_str = json.dumps(formatted_data, indent=2, ensure_ascii=False)

        output_path = None
        if opts.destination == OutputDestination.FILE_PATH and opts.output_path:
            output_path = opts.output_path
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output_str)

        return ExportResult(
            format_id=self.format_id,
            destination=opts.destination,
            content=output_str,
            output_path=output_path,
        )

    def extract_chunks(self, document: DocumentIR) -> List[RagChunk]:
        """Extract semantic blocks from DocumentIR into RagChunk instances."""
        chunks: List[RagChunk] = []
        doc_name = document.metadata.name or "document"
        heading_stack: List[str] = []

        for page in document.pages:
            for block in page.blocks:
                b_type = getattr(block, "block_type", getattr(block, "type", BlockType.TEXT))
                # Update heading hierarchy stack
                if b_type == BlockType.HEADING:
                    b_text = getattr(block, "text", "").strip()
                    heading_stack.append(b_text)
                    chunk_type = "heading"
                elif b_type == BlockType.TABLE:
                    chunk_type = "table"
                elif b_type == BlockType.FIGURE:
                    chunk_type = "figure"
                elif b_type == BlockType.FORMULA:
                    chunk_type = "formula"
                else:
                    chunk_type = "paragraph"

                b_text = block.text.strip()
                if not b_text and not getattr(block, "table_data", None):
                    continue

                bbox_coords = None
                if block.bbox:
                    bbox_coords = [
                        round(block.bbox.left, 4),
                        round(block.bbox.top, 4),
                        round(block.bbox.right, 4),
                        round(block.bbox.bottom, 4),
                    ]

                doc_id = getattr(document.metadata, "id", "doc_unknown")
                meta = RagChunkMetadata(
                    document_id=doc_id,
                    document_name=doc_name,
                    page_index=page.page_index,
                    chunk_type=chunk_type,
                    bbox=bbox_coords,
                    heading_hierarchy=list(heading_stack),
                    figure_caption=getattr(block, "caption", None),
                    formula_latex=getattr(block, "latex", None),
                    table_matrix=getattr(block, "table_matrix", None),
                )

                chunk_id = f"{doc_id}_p{page.page_index}_b{block.id or len(chunks)}"
                chunks.append(RagChunk(chunk_id=chunk_id, text=b_text, metadata=meta))

        return chunks

    @classmethod
    def to_langchain(cls, chunks: List[RagChunk]) -> List[Dict[str, Any]]:
        """Convert chunks to LangChain Document schema."""
        return [
            {
                "page_content": c.text,
                "metadata": c.metadata.model_dump(),
            }
            for c in chunks
        ]

    @classmethod
    def to_llamaindex(cls, chunks: List[RagChunk]) -> List[Dict[str, Any]]:
        """Convert chunks to LlamaIndex TextNode schema."""
        return [
            {
                "id_": c.chunk_id,
                "text": c.text,
                "extra_info": c.metadata.model_dump(),
            }
            for c in chunks
        ]

    @classmethod
    def to_vector_records(cls, chunks: List[RagChunk], vector_db: str) -> List[Dict[str, Any]]:
        """Convert chunks to Chroma / Qdrant / Pinecone vector records."""
        records = []
        for c in chunks:
            if vector_db == "qdrant":
                records.append({
                    "id": c.chunk_id,
                    "payload": {
                        "text": c.text,
                        **c.metadata.model_dump(),
                    }
                })
            elif vector_db == "pinecone":
                records.append({
                    "id": c.chunk_id,
                    "metadata": {
                        "text": c.text,
                        **c.metadata.model_dump(),
                    }
                })
            else:
                # Chroma format
                records.append({
                    "id": c.chunk_id,
                    "document": c.text,
                    "metadata": c.metadata.model_dump(),
                })
        return records
