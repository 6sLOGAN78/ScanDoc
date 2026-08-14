"""
Synchronous conversion endpoint for scanDOC REST API server.
"""

import os
from pathlib import Path
import tempfile
import uuid

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import PlainTextResponse, Response

from scandoc.exporters import default_exporter_registry, ExportOptions
from scandoc.pipelines import DocumentPipeline, PipelineConfig, OrderingMode
from scandoc.server.taxonomy import ServerErrorCode

router = APIRouter(prefix="/api/v1", tags=["Conversion"])


def sanitize_filename(filename: str) -> str:
    """Sanitize uploaded filename against path traversal attacks."""
    normalized = str(filename).replace("\\", "/")
    base = Path(normalized).name
    clean = "".join(c for c in base if c.isalnum() or c in (".", "_", "-")).strip()
    return clean or "uploaded_document"


@router.post("/convert")
async def convert_document(
    request: Request,
    file: UploadFile = File(...),
    format: str = Form("markdown"),
    device: str = Form("auto"),
    provider: str = Form(None),
    model: str = Form(None),
):
    """
    Synchronous document conversion endpoint.
    
    Accepts multipart document file upload and returns converted output content.
    """
    fmt_name = format.lower()
    try:
        default_exporter_registry.get_exporter(fmt_name)
    except Exception as e:
        valid_fmts = ", ".join([exp.format_id for exp in default_exporter_registry.list_exporters()])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": ServerErrorCode.UNSUPPORTED_FORMAT.value,
                "message": f"Unsupported format '{format}'. Supported formats: [{valid_fmts}]",
            },
        ) from e

    # Read uploaded file content
    content_bytes = await file.read()

    # Check payload size limit
    server_config = getattr(request.app.state, "server_config", None)
    max_size = server_config.max_upload_bytes if server_config else 52428800
    if len(content_bytes) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error_code": ServerErrorCode.PAYLOAD_TOO_LARGE.value,
                "message": f"Upload size ({len(content_bytes)} bytes) exceeds maximum limit ({max_size} bytes).",
            },
        )

    clean_name = sanitize_filename(file.filename or "doc.pdf")
    ext = Path(clean_name).suffix or ".pdf"

    # Write to safe temporary location
    temp_dir = tempfile.gettempdir()
    temp_path = Path(temp_dir) / f"scandoc_sync_{uuid.uuid4()}{ext}"
    temp_path.write_bytes(content_bytes)

    try:
        pipeline = DocumentPipeline(config=PipelineConfig(max_workers=1, ordering_mode=OrderingMode.ORDERED))
        p_result = pipeline.process(temp_path)

        if p_result.status != "success" or not p_result.document_ir:
            err_msg = "; ".join(p_result.errors) if p_result.errors else "Document pipeline conversion failed."
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": ServerErrorCode.PROCESSING_ERROR.value,
                    "message": err_msg,
                },
            )

        export_res = default_exporter_registry.export(p_result.document_ir, ExportOptions(format_id=fmt_name))
        output_data = export_res.content

        if isinstance(output_data, bytes):
            return Response(content=output_data, media_type="application/octet-stream")
        else:
            return PlainTextResponse(content=str(output_data))

    finally:
        try:
            if temp_path.exists():
                os.remove(temp_path)
        except Exception:
            pass
