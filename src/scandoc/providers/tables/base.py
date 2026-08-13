"""
Abstract Base Class contract for table structure recognition providers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, List, Optional, Union

from scandoc.models.geometry import BoundingBox
from scandoc.providers.tables.models import TableStructureConfig, TableStructureResult


class BaseTableProvider(ABC):
    """
    Abstract Base Class for Table Detection & Structure Recognition providers.
    
    Decouples table structure recognition models (SLANet, Table Transformer, TATR, PaddleStructure, Surya)
    from scanDOC DocumentIR assembly and pipeline logic.
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Return unique provider identifier (e.g. 'slanet_table')."""
        pass

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Return specific model checkpoint name (e.g. 'SLANet-DocTable')."""
        pass

    @property
    def is_available(self) -> bool:
        """Return True if engine dependencies and model weights are available."""
        return True

    @abstractmethod
    def initialize(self, config: Optional[TableStructureConfig] = None) -> None:
        """Initialize provider models and configuration."""
        pass

    @abstractmethod
    def infer_table_structure(
        self,
        image_input: Union[str, Path, bytes, bytearray, BinaryIO],
        table_bbox: Optional[BoundingBox] = None,
        page_index: int = 0,
        config: Optional[TableStructureConfig] = None,
    ) -> TableStructureResult:
        """
        Infer table row/column grid, cell boundaries, and row/col spans.
        
        Args:
            image_input: File path, bytes buffer, or binary stream of page image.
            table_bbox: Optional bounding box of table region on page.
            page_index: Target 0-indexed document page number.
            config: Optional override configuration for this inference run.
            
        Returns:
            TableStructureResult containing grid cells, rows, columns, and spans.
        """
        pass

    def infer_batch(
        self,
        image_inputs: List[Union[str, Path, bytes, bytearray, BinaryIO]],
        config: Optional[TableStructureConfig] = None,
    ) -> List[TableStructureResult]:
        """
        Perform batch table structure inference.
        """
        return [
            self.infer_table_structure(img, page_index=idx, config=config)
            for idx, img in enumerate(image_inputs)
        ]

    def shutdown(self) -> None:
        """Release allocated model sessions or resources."""
        pass

    def __enter__(self) -> "BaseTableProvider":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown()
