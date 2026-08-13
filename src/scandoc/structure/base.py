"""
Abstract Base Class contract for reading order engines and hierarchy reconstructors.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from scandoc.models import DocumentIR, Page
from scandoc.providers.layout.models import LayoutResult
from scandoc.structure.models import DocumentHierarchy, ReadingOrderResult


class BaseReadingOrderEngine(ABC):
    """
    Abstract Base Class for Reading Order & Document Structure Reconstruction engines.
    
    Determines reading sequence and hierarchical relationships from spatial page blocks.
    Does NOT overwrite native extraction order or rely on ML/LLM inference.
    """

    @property
    @abstractmethod
    def engine_id(self) -> str:
        """Return unique string identifier of reading order engine."""
        pass

    @abstractmethod
    def order_page_blocks(
        self,
        page: Page,
        layout_result: Optional[LayoutResult] = None,
    ) -> ReadingOrderResult:
        """
        Determine human reading order sequence for blocks on a single page.
        
        Args:
            page: Target DocumentIR Page containing blocks.
            layout_result: Optional visual layout predictions from Phase 9.
            
        Returns:
            ReadingOrderResult containing ordered block IDs and sequence metadata.
        """
        pass

    def order_document_pages(
        self,
        doc: DocumentIR,
        layout_results: Optional[List[LayoutResult]] = None,
    ) -> List[ReadingOrderResult]:
        """
        Determine reading order sequence across all pages in a document.
        """
        results: List[ReadingOrderResult] = []
        for idx, page in enumerate(doc.pages):
            layout_res = layout_results[idx] if (layout_results and idx < len(layout_results)) else None
            results.append(self.order_page_blocks(page, layout_result=layout_res))
        return results

    @abstractmethod
    def reconstruct_hierarchy(
        self,
        doc: DocumentIR,
        reading_orders: Optional[List[ReadingOrderResult]] = None,
    ) -> DocumentHierarchy:
        """
        Build hierarchical section tree from ordered document blocks.
        """
        pass
