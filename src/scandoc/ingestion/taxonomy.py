"""
Taxonomy enums for source data classification (NATIVE vs MODEL_DERIVED).
"""

from enum import Enum


class SourceDataType(str, Enum):
    """
    Classification of data origin (native document structure vs model-derived outputs).
    """
    NATIVE = "native"
    INFERRED = "inferred"
    MODEL_DERIVED = "model_derived"
    USER_PROVIDED = "user_provided"
