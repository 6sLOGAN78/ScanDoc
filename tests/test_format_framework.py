"""
Unit test suite for Phase 4: Multi-Format Ingestion Framework.
"""

import pytest
from scandoc.models import DocumentIR
from scandoc.formats import (
    FormatDetector,
    FormatRegistry,
    BaseFormatProvider,
    FormatDetectionResult,
    UnsupportedFormatError,
    InvalidFileError,
    ProviderExtractionError,
)
from scandoc.formats.providers import (
    PDFFormatProvider,
    DOCXFormatProvider,
    PPTXFormatProvider,
    HTMLFormatProvider,
    ImageFormatProvider,
    TXTFormatProvider,
    MarkdownFormatProvider,
)
from fixtures.pdf_fixtures import generate_digital_pdf_bytes


def test_magic_bytes_detection_pdf():
    """Test magic bytes detection for PDF document."""
    pdf_bytes = b"%PDF-1.7\n%\xff\xff\xff\xff\n"
    res = FormatDetector.detect(pdf_bytes)
    assert res.detected_format == "pdf"
    assert res.mime_type == "application/pdf"
    assert res.extension == ".pdf"
    assert res.detection_method == "magic_bytes"
    assert res.confidence == 1.0


def test_magic_bytes_detection_images():
    """Test magic bytes detection for PNG, JPEG, WEBP, and TIFF images."""
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    res_png = FormatDetector.detect(png_bytes)
    assert res_png.detected_format == "image"
    assert res_png.mime_type == "image/png"

    jpg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    res_jpg = FormatDetector.detect(jpg_bytes)
    assert res_jpg.detected_format == "image"
    assert res_jpg.mime_type == "image/jpeg"

    webp_bytes = b"RIFF\x00\x00\x00\x00WEBPVP8 "
    res_webp = FormatDetector.detect(webp_bytes)
    assert res_webp.detected_format == "image"
    assert res_webp.mime_type == "image/webp"

    tiff_bytes = b"II*\x00\x08\x00\x00\x00"
    res_tiff = FormatDetector.detect(tiff_bytes)
    assert res_tiff.detected_format == "image"
    assert res_tiff.mime_type == "image/tiff"


def test_magic_bytes_detection_html():
    """Test magic bytes detection for HTML documents."""
    html_bytes = b"<!DOCTYPE html><html><head><title>Test</title></head></html>"
    res = FormatDetector.detect(html_bytes)
    assert res.detected_format == "html"
    assert res.mime_type == "text/html"


def test_extension_detection_fallback(tmp_path):
    """Test extension detection fallback when magic bytes are ambiguous or plain text."""
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("Plain text sample file content.", encoding="utf-8")
    res = FormatDetector.detect(str(txt_file))
    assert res.detected_format in ("txt", "markdown")
    assert res.extension == ".txt"


def test_explicit_format_override():
    """Test explicit user format override."""
    dummy_bytes = b"Some random text content"
    res = FormatDetector.detect(dummy_bytes, override_format="pdf")
    assert res.detected_format == "pdf"
    assert res.detection_method == "explicit_override"
    assert res.confidence == 1.0


def test_unsupported_format_error():
    """Test unsupported format error for unknown binary format."""
    unknown_binary = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a"
    with pytest.raises(UnsupportedFormatError):
        FormatDetector.detect(unknown_binary)


def test_invalid_file_error():
    """Test 0-byte file input raises InvalidFileError."""
    with pytest.raises(InvalidFileError):
        FormatDetector.detect(b"")


def test_registry_provider_registration_and_lookup():
    """Test FormatRegistry provider registration, listing, and lookup."""
    registry = FormatRegistry(register_defaults=True)
    providers = registry.list_providers()
    
    # 7 default providers
    assert len(providers) == 7
    provider_names = {p.name for p in providers}
    assert provider_names == {"pdf", "docx", "pptx", "html", "image", "txt", "markdown"}

    # Test PDF provider lookup
    pdf_bytes = generate_digital_pdf_bytes(1, "Registry Test")
    pdf_provider = registry.get_provider_for(pdf_bytes)
    assert pdf_provider.format_name == "pdf"
    assert pdf_provider.is_fully_implemented is True


def test_custom_third_party_provider_registration():
    """Test dynamic registration and unregistration of custom third-party format providers."""
    class CustomEPUBProvider(BaseFormatProvider):
        @property
        def format_name(self) -> str:
            return "epub"
        @property
        def supported_extensions(self) -> set[str]:
            return {".epub"}
        @property
        def supported_mime_types(self) -> set[str]:
            return {"application/epub+zip"}
        def parse(self, source, file_path=None) -> DocumentIR:
            raise NotImplementedError()

    registry = FormatRegistry(register_defaults=False)
    custom_prov = CustomEPUBProvider()
    registry.register(custom_prov)
    
    assert len(registry.list_providers()) == 1
    assert registry.list_providers()[0].name == "epub"
    
    # Unregister
    removed = registry.unregister("epub")
    assert removed is custom_prov
    assert len(registry.list_providers()) == 0


def test_pdf_format_provider_integration():
    """Test parsing a digital PDF through FormatRegistry -> PDFFormatProvider -> DocumentIR."""
    pdf_bytes = generate_digital_pdf_bytes(page_count=1, text="Format Registry Integration PDF")
    registry = FormatRegistry(register_defaults=True)
    
    doc: DocumentIR = registry.parse(pdf_bytes, file_path="sample.pdf")
    assert isinstance(doc, DocumentIR)
    assert doc.metadata.name == "sample.pdf"
    assert len(doc.pages) == 1
    assert "Format Registry Integration PDF" in doc.pages[0].blocks[0].text


def test_placeholder_stub_provider_behavior():
    """Test Phase 18 fully implemented format providers behavior."""
    docx_prov = DOCXFormatProvider()
    assert docx_prov.is_fully_implemented is True
    assert ".docx" in docx_prov.supported_extensions

    pptx_prov = PPTXFormatProvider()
    assert pptx_prov.is_fully_implemented is True

    html_prov = HTMLFormatProvider()
    assert html_prov.is_fully_implemented is True

    img_prov = ImageFormatProvider()
    assert img_prov.is_fully_implemented is True

    txt_prov = TXTFormatProvider()
    assert txt_prov.is_fully_implemented is True

    md_prov = MarkdownFormatProvider()
    assert md_prov.is_fully_implemented is True
