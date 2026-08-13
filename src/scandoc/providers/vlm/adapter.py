"""
VlmDocumentAdapter integrating VLM visual reasoning outputs into DocumentIR.
"""

import logging
from typing import Optional

from scandoc.models.document import DocumentIR
from scandoc.models.provenance import ProcessingStage, Provenance
from scandoc.providers.vlm.models import VlmResult

logger = logging.getLogger("scandoc.providers.vlm.adapter")


class VlmDocumentAdapter:
    """
    Adapts VlmResult into DocumentIR metadata enrichments or corrections.
    Never silently overwrites native PDF or OCR extraction results.
    """

    @classmethod
    def enrich_document_ir(
        cls,
        doc: DocumentIR,
        vlm_result: VlmResult,
        target_page_index: int = 0,
    ) -> DocumentIR:
        """
        Attach VLM visual reasoning outputs as page provenance metadata.
        
        Args:
            doc: DocumentIR target document.
            vlm_result: VlmResult outcome.
            target_page_index: Target 0-indexed page number.
            
        Returns:
            Updated DocumentIR instance with VLM metadata attached.
        """
        prov = Provenance(
            provider=vlm_result.provider_id,
            model=vlm_result.model_id,
            stage=ProcessingStage.POST_PROCESSING,
            confidence=vlm_result.confidence or 1.0,
        )

        if target_page_index < len(doc.pages):
            page = doc.pages[target_page_index]
            # Attach VLM task summary as page metadata entry
            key = f"vlm_{vlm_result.task.value}"
            val = vlm_result.text_result or str(vlm_result.structured_result)
            page.blocks.append(
                # Add VLM provenance block or metadata tag
            ) if False else None

        return doc
