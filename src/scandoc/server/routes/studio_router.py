"""
API routes serving scanDOC Visual Layout Inspector Studio (scandoc studio).
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import HTMLResponse

from scandoc.exporters import ExportOptions, default_exporter_registry
from scandoc.models import BlockType
from scandoc.pipelines import DocumentPipeline, PipelineConfig

logger = logging.getLogger("scandoc.server.routes.studio")

studio_router = APIRouter(tags=["Studio"])

STATIC_DIR = Path(__file__).parent.parent / "static"


@studio_router.get("/studio", response_class=HTMLResponse)
async def get_studio_ui():
    """Serve the single-page Visual Layout Inspector Studio UI."""
    html_file = STATIC_DIR / "studio.html"
    if not html_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Studio HTML asset missing.")
    return HTMLResponse(content=html_file.read_text(encoding="utf-8"))


@studio_router.post("/api/studio/inspect")
async def inspect_document_studio(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Process uploaded document and return layout bounding boxes, Markdown, HTML, and DocumentIR.
    """
    try:
        content_bytes = await file.read()
        pipeline = DocumentPipeline(config=PipelineConfig(routing_mode="adaptive", export_format="markdown"))
        result = pipeline.process(content_bytes, file_name=file.filename)

        if not result.document_ir:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to parse document IR.")

        # Render HTML export
        html_res = default_exporter_registry.export(result.document_ir, options=ExportOptions(format_id="html"))
        md_res = default_exporter_registry.export(result.document_ir, options=ExportOptions(format_id="markdown"))

        # Build Page Layout Overlay JSON
        pages_layout: List[Dict[str, Any]] = []
        for page in result.document_ir.pages:
            page_blocks: List[Dict[str, Any]] = []
            for block in page.blocks:
                b_type = getattr(block, "block_type", getattr(block, "type", BlockType.TEXT))
                
                # Assign color coding
                if b_type in (BlockType.HEADING, getattr(BlockType, "TITLE", "title")):
                    color = "#ef4444"  # Red
                elif b_type == BlockType.TABLE:
                    color = "#10b981"  # Green
                elif b_type == BlockType.FORMULA:
                    color = "#8b5cf6"  # Purple
                elif b_type == BlockType.FIGURE:
                    color = "#f59e0b"  # Orange
                else:
                    color = "#3b82f6"  # Blue

                bbox_arr = None
                if block.bbox:
                    bbox_arr = [
                        round(block.bbox.left, 4),
                        round(block.bbox.top, 4),
                        round(block.bbox.right, 4),
                        round(block.bbox.bottom, 4),
                    ]

                page_blocks.append({
                    "id": block.id,
                    "type": b_type.value if hasattr(b_type, "value") else str(b_type),
                    "bbox": bbox_arr,
                    "color": color,
                    "text": getattr(block, "text", "")[:100],
                    "confidence": 0.95,
                })

            pages_layout.append({
                "page_index": page.page_index,
                "width": page.width,
                "height": page.height,
                "blocks": page_blocks,
            })

        return {
            "document_id": result.document_id,
            "status": "success",
            "markdown": md_res.content,
            "html": html_res.content,
            "pages": pages_layout,
        }

    except Exception as e:
        logger.error("Studio inspection error: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
