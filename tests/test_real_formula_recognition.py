"""
Comprehensive test suite for Phase 31: Real LaTeX Formula & Mathematical Content Vision Engine Integration.
"""

import io
from pathlib import Path
import tempfile
from PIL import Image, ImageDraw
import pytest

from scandoc.exporters import HtmlExporter, MarkdownExporter
from scandoc.models import DocumentIR, DocumentMetadata, Page
from scandoc.models.blocks import FormulaBlock, FormulaFormat
from scandoc.models.geometry import BoundingBox
from scandoc.models_mgmt import default_model_manager
from scandoc.models_mgmt.taxonomy import TaskType
from scandoc.providers.formulas import (
    FormulaConfig,
    FormulaResult,
    FormulaType,
    LocalFormulaProvider,
    MathFormat,
    formula_result_to_document_ir,
)
from scandoc.models.provenance import ProcessingStage


@pytest.fixture
def formula_provider():
    prov = LocalFormulaProvider()
    if not prov.is_available:
        pytest.skip("onnxruntime dependency not installed.")
    return prov


@pytest.fixture
def formula_crop_image_bytes():
    """Generate a clean synthetic formula image containing a mathematical expression."""
    img = Image.new("RGB", (400, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 35), "x^2 + y^2 = z^2", fill=(0, 0, 0))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# 1. Local Formula Provider Capability & Availability Test
def test_local_formula_provider_initialization(formula_provider):
    """Verify Local Formula Provider initialization and metadata."""
    assert formula_provider.provider_id == "local_formula_recognizer"
    assert "LaTeX-OCR" in formula_provider.model_id


# 2. Real Formula Model Inference Test
def test_real_formula_inference_on_image(formula_provider, formula_crop_image_bytes):
    """Verify formula image crop input yields valid LaTeX formula result."""
    bbox = BoundingBox(left=0.1, top=0.3, right=0.9, bottom=0.5, is_normalized=True)
    result: FormulaResult = formula_provider.recognize_formula(
        formula_crop_image_bytes, bbox=bbox, formula_type=FormulaType.DISPLAY, page_index=0
    )

    assert result is not None
    assert result.provider_id == "local_formula_recognizer"
    assert result.representation.format == MathFormat.LATEX
    assert len(result.representation.value) > 0
    assert result.confidence >= 0.0
    assert result.bbox.left == 0.1
    assert result.bbox.top == 0.3


# 3. Formula Result to DocumentIR Conversion Test
def test_formula_result_to_document_ir(formula_provider, formula_crop_image_bytes):
    """Verify FormulaResult maps into DocumentIR FormulaBlock model."""
    result = formula_provider.recognize_formula(formula_crop_image_bytes, page_index=0)
    formula_block: FormulaBlock = formula_result_to_document_ir(result)

    assert formula_block is not None
    assert formula_block.expression == result.representation.value
    assert formula_block.format == FormulaFormat.LATEX
    assert formula_block.provenance is not None
    assert formula_block.provenance.provider == "local_formula_recognizer"


# 4. Formula Exporting to Markdown and HTML Test
def test_formula_export_to_markdown_and_html(formula_provider, formula_crop_image_bytes):
    """Verify FormulaBlock exports into Markdown math blocks and HTML formatting."""
    result = formula_provider.recognize_formula(formula_crop_image_bytes, page_index=0)
    formula_block = formula_result_to_document_ir(result)
    formula_block.expression = r"x^2 + y^2 = z^2"

    doc_ir = DocumentIR(
        metadata=DocumentMetadata(id="test_doc", name="Formula Doc"),
        pages=[Page(page_index=0, page_number=1, width=600, height=400, blocks=[formula_block])],
    )

    md_exporter = MarkdownExporter()
    md_out = md_exporter.export(doc_ir)
    assert "$$" in md_out.content or "x^2 + y^2 = z^2" in md_out.content

    html_exporter = HtmlExporter()
    html_out = html_exporter.export(doc_ir)
    assert "x^2 + y^2 = z^2" in html_out.content


# 5. ModelManager Spec Lifecycle Test for pix2text_formula
def test_model_manager_formula_spec_lifecycle():
    """Verify pix2text_formula is registered in ModelRegistry for TaskType.FORMULA."""
    mgr = default_model_manager
    models = mgr.list_available_models(task=TaskType.FORMULA)

    formula_ids = [m.model_id for m in models]
    assert "pix2text_formula" in formula_ids
