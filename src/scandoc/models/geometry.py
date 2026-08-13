"""
Spatial geometry primitives and coordinate system abstractions for scanDOC DocumentIR.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class CoordOrigin(str, Enum):
    """Origin point of the coordinate system."""
    TOP_LEFT = "TOP_LEFT"      # Standard web/image space (y down)
    BOTTOM_LEFT = "BOTTOM_LEFT"  # PDF native space (y up)


class SizeUnit(str, Enum):
    """Measurement unit for page dimensions and coordinates."""
    NORMALIZED = "NORMALIZED"  # 0.0 to 1.0 relative coordinates
    POINTS = "POINTS"          # 72 points per inch (PDF standard)
    PIXELS = "PIXELS"          # Raster pixel coordinates
    INCHES = "INCHES"
    MM = "MM"


class Point2D(BaseModel):
    """2D spatial point coordinate."""
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")


class BoundingBox(BaseModel):
    """
    Page-indexed spatial bounding box.
    Coordinates represent [left, top, right, bottom].
    """
    left: float = Field(..., description="Left boundary (x_min)")
    top: float = Field(..., description="Top boundary (y_min)")
    right: float = Field(..., description="Right boundary (x_max)")
    bottom: float = Field(..., description="Bottom boundary (y_max)")
    page_index: int = Field(0, ge=0, description="0-indexed page number")
    coord_origin: CoordOrigin = Field(
        CoordOrigin.TOP_LEFT,
        description="Origin point of coordinate space"
    )
    unit: SizeUnit = Field(
        SizeUnit.NORMALIZED,
        description="Measurement unit of coordinate space"
    )
    is_normalized: bool = Field(
        True,
        description="Whether left, top, right, bottom are normalized between 0.0 and 1.0"
    )

    @model_validator(mode="after")
    def validate_box_geometry(self) -> "BoundingBox":
        """Validate bounding box coordinate consistency and bounds."""
        if self.left > self.right:
            raise ValueError(
                f"Invalid bounding box: left ({self.left}) cannot be greater than right ({self.right})"
            )
        if self.top > self.bottom:
            raise ValueError(
                f"Invalid bounding box: top ({self.top}) cannot be greater than bottom ({self.bottom})"
            )
        
        if self.is_normalized:
            # Allow slight floating-point tolerance (e.g., 1.0001)
            epsilon = 1e-4
            for name, val in [
                ("left", self.left),
                ("top", self.top),
                ("right", self.right),
                ("bottom", self.bottom),
            ]:
                if val < -epsilon or val > 1.0 + epsilon:
                    raise ValueError(
                        f"Normalized bounding box {name} ({val}) must be between 0.0 and 1.0"
                    )
        return self

    @property
    def width(self) -> float:
        """Calculate width of bounding box."""
        return self.right - self.left

    @property
    def height(self) -> float:
        """Calculate height of bounding box."""
        return self.bottom - self.top

    @property
    def area(self) -> float:
        """Calculate area of bounding box."""
        return self.width * self.height

    def to_tuple(self) -> tuple[float, float, float, float]:
        """Return box coordinates as (left, top, right, bottom) tuple."""
        return (self.left, self.top, self.right, self.bottom)
