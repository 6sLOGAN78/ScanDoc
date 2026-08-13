"""
Helper utilities to generate realistic test PDF byte streams for testing PdfInspector.
Uses fitz (PyMuPDF) in test fixtures to construct valid digital, scanned, and hybrid PDFs.
"""

import fitz


def generate_digital_pdf_bytes(page_count: int = 1, text: str = "Annual Financial Report 2025") -> bytes:
    """Generate in-memory digital PDF with native vector text."""
    doc = fitz.open()
    for _ in range(page_count):
        page = doc.new_page(width=612, height=792)  # Standard Letter 8.5x11 inch at 72 dpi
        page.insert_text((100, 100), text, fontsize=18)
        page.insert_text((100, 150), "Section 1. Executive Summary and Revenue Growth.", fontsize=12)
        page.insert_text((100, 200), "Total revenue for fiscal year 2025 exceeded $4.2 billion USD.", fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def generate_image_pdf_bytes(page_count: int = 1) -> bytes:
    """Generate in-memory scanned PDF containing full-page raster image and no text."""
    doc = fitz.open()
    pix = fitz.Pixmap(fitz.csRGB, (0, 0, 200, 200), False)
    pix.clear_with(200)
    img_bytes = pix.tobytes("png")

    for _ in range(page_count):
        page = doc.new_page(width=612, height=792)
        rect = fitz.Rect(0, 0, 612, 792)  # Covers entire page
        page.insert_image(rect, stream=img_bytes)
        
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def generate_hybrid_pdf_bytes() -> bytes:
    """Generate in-memory hybrid PDF with native text AND an embedded figure image."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    
    # Native Text
    page.insert_text((100, 100), "Executive Summary with Figure", fontsize=18)
    page.insert_text((100, 140), "Below is Figure 1 representing the system layout diagram.", fontsize=12)

    # Image Figure
    pix = fitz.Pixmap(fitz.csRGB, (0, 0, 100, 100), False)
    pix.clear_with(150)
    img_bytes = pix.tobytes("png")
    rect = fitz.Rect(100, 200, 400, 500)  # Mid-page figure box
    page.insert_image(rect, stream=img_bytes)

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes
