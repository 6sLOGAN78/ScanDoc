"""
Format provider implementations for scanDOC.
"""

from scandoc.formats.providers.docx_provider import DOCXFormatProvider
from scandoc.formats.providers.html_provider import HTMLFormatProvider
from scandoc.formats.providers.image_provider import ImageFormatProvider
from scandoc.formats.providers.markdown_provider import MarkdownFormatProvider
from scandoc.formats.providers.pdf_provider import PDFFormatProvider
from scandoc.formats.providers.pptx_provider import PPTXFormatProvider
from scandoc.formats.providers.txt_provider import TXTFormatProvider

__all__ = [
    "PDFFormatProvider",
    "DOCXFormatProvider",
    "PPTXFormatProvider",
    "HTMLFormatProvider",
    "ImageFormatProvider",
    "TXTFormatProvider",
    "MarkdownFormatProvider",
]
