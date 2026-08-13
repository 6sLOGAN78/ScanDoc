"""
Converter mapping FormulaResult models into DocumentIR FormulaBlock objects.
"""

from typing import Optional

from scandoc.models.blocks import FormulaBlock, FormulaFormat
from scandoc.models.provenance import ProcessingStage, Provenance
from scandoc.providers.formulas.models import FormulaResult
from scandoc.providers.formulas.taxonomy import FormulaType, MathFormat


def formula_result_to_document_ir(
    formula_res: FormulaResult,
    target_formula_block: Optional[FormulaBlock] = None,
) -> FormulaBlock:
    """
    Convert FormulaResult into DocumentIR FormulaBlock model.
    
    Preserves LaTeX/MathML syntax, bounding box, equation format, and provenance metadata.
    """
    prov = Provenance(
        provider=formula_res.provider_id,
        model=formula_res.model_id,
        stage=ProcessingStage.POST_PROCESSING,
        confidence=formula_res.confidence,
    )

    # Map MathFormat to DocumentIR FormulaFormat
    fmt_map = {
        MathFormat.LATEX: FormulaFormat.LATEX,
        MathFormat.MATHML: FormulaFormat.MATHML,
        MathFormat.PLAINTEXT: FormulaFormat.TEXT,
        MathFormat.UNKNOWN: FormulaFormat.TEXT,
    }
    ir_fmt = fmt_map.get(formula_res.representation.format, FormulaFormat.LATEX)

    is_inline = (formula_res.formula_type == FormulaType.INLINE)

    if target_formula_block is not None:
        target_formula_block.expression = formula_res.representation.value
        target_formula_block.format = ir_fmt
        target_formula_block.is_inline = is_inline
        target_formula_block.bbox = formula_res.bbox
        target_formula_block.provenance = prov
        return target_formula_block

    return FormulaBlock(
        id=formula_res.formula_id,
        expression=formula_res.representation.value,
        format=ir_fmt,
        is_inline=is_inline,
        bbox=formula_res.bbox,
        provenance=prov,
    )
