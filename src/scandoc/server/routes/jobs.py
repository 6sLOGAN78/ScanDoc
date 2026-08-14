"""
Asynchronous Job management routes for scanDOC REST API server.
"""

from pathlib import Path
import tempfile
import uuid

from fastapi import APIRouter, File, Form, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import PlainTextResponse

from scandoc.exporters import default_exporter_registry
from scandoc.server.models import ConvertRequest, JobResponse, JobStatusResponse
from scandoc.server.routes.convert import sanitize_filename
from scandoc.server.taxonomy import JobStatus, ServerErrorCode

router = APIRouter(prefix="/api/v1/jobs", tags=["Async Jobs"])


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=JobResponse)
async def create_job(
    request: Request,
    file: UploadFile = File(...),
    format: str = Form("markdown"),
    device: str = Form("auto"),
    provider: str = Form(None),
    model: str = Form(None),
    webhook_url: str = Form(None),
):
    """
    Submit an asynchronous document processing job.
    
    Returns 202 Accepted with a unique job ID for progress tracking.
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

    content_bytes = await file.read()
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

    temp_dir = tempfile.gettempdir()
    temp_path = Path(temp_dir) / f"scandoc_async_{uuid.uuid4()}{ext}"
    temp_path.write_bytes(content_bytes)

    job_mgr = request.app.state.job_manager
    convert_req = ConvertRequest(
        format=fmt_name,
        device=device,
        provider=provider,
        model=model,
        webhook_url=webhook_url,
    )

    job = job_mgr.create_job(file_name=clean_name, temp_path=temp_path, request=convert_req)

    return JobResponse(
        job_id=job.job_id,
        status=job.status,
        created_at=job.created_at,
        message="Job successfully queued for background processing.",
    )


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str, request: Request):
    """
    Get progress and status of a processing job.
    """
    job_mgr = request.app.state.job_manager
    status_resp = job_mgr.get_job_status(job_id)
    if not status_resp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": ServerErrorCode.NOT_FOUND.value,
                "message": f"Job '{job_id}' not found.",
            },
        )
    return status_resp


@router.get("/{job_id}/result")
def get_job_result(job_id: str, request: Request, format: str = None):
    """
    Retrieve exported conversion result for a completed job.
    """
    job_mgr = request.app.state.job_manager
    job_status = job_mgr.get_job_status(job_id)
    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": ServerErrorCode.NOT_FOUND.value,
                "message": f"Job '{job_id}' not found.",
            },
        )

    if job_status.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": ServerErrorCode.CONFLICT.value,
                "message": f"Job '{job_id}' is not in completed state (current status: '{job_status.status.value}').",
            },
        )

    content, err = job_mgr.get_job_result(job_id, format_override=format)
    if err or content is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": ServerErrorCode.PROCESSING_ERROR.value,
                "message": err or "Failed to retrieve job result.",
            },
        )

    if isinstance(content, bytes):
        return Response(content=content, media_type="application/octet-stream")
    else:
        return PlainTextResponse(content=str(content))


@router.post("/{job_id}/cancel")
def cancel_job(job_id: str, request: Request):
    """
    Cancel an active or queued processing job.
    """
    job_mgr = request.app.state.job_manager
    success, msg = job_mgr.cancel_job(job_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": ServerErrorCode.CONFLICT.value,
                "message": msg,
            },
        )
    return {"job_id": job_id, "status": JobStatus.CANCELLED.value, "message": msg}
