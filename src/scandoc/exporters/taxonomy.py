"""
Taxonomy enums for exporter output strategies and image handling mechanisms.
"""

from enum import Enum


class ImageHandlingStrategy(str, Enum):
    """
    Image resolution strategy for export outputs.
    """
    EMBED_BASE64 = "embed_base64"
    FILE_REFERENCE = "file_reference"


class OutputDestination(str, Enum):
    """
    Export output payload target.
    """
    STRING = "string"
    BYTES = "bytes"
    FILE_PATH = "file_path"
