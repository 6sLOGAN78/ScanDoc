"""
Manifest definitions for dataset discovery and corpus management.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from scandoc.benchmarks.taxonomy import DocumentType


class ManifestDocument(BaseModel):
    """Document entry within dataset manifest."""
    id: str = Field(..., description="Unique document ID")
    path: str = Field(..., description="Path to document file")
    doc_type: DocumentType = Field(DocumentType.DIGITAL_PDF, description="Document classification type")
    page_count: int = Field(1, ge=1, description="Expected page count")
    file_size_bytes: int = Field(0, ge=0, description="File size in bytes")
    ground_truth_path: Optional[str] = Field(None, description="Optional path to ground truth reference")
    tags: List[str] = Field(default_factory=list, description="Tags/metadata associated with document")


class DocumentCorpusManifest(BaseModel):
    """Corpus manifest describing benchmark dataset."""
    dataset_name: str = Field("scanDOC Local Benchmark Corpus", description="Name of dataset")
    version: str = Field("1.0.0", description="Corpus version")
    description: str = Field("Comprehensive benchmark document corpus", description="Description")
    documents: List[ManifestDocument] = Field(default_factory=list, description="List of corpus documents")

    def find_document(self, doc_id: str) -> Optional[ManifestDocument]:
        for doc in self.documents:
            if doc.id == doc_id:
                return doc
        return None
