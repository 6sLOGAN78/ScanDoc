"""
Exception classes for Comprehensive Exporters & Output Serialization Pipeline.
"""


class ExporterError(Exception):
    """Base exception for all document export errors."""
    pass


class UnsupportedExporterFormatError(ExporterError):
    """Raised when an exporter format is unknown or unregistered."""
    pass


class SerializationError(ExporterError):
    """Raised when DocumentIR serialization fails."""
    pass


class AssetResolutionError(ExporterError):
    """Raised when an image asset cannot be resolved or saved."""
    pass
