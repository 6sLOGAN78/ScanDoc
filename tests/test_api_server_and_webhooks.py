"""
Comprehensive test suite for Phase 25: REST / HTTP API Web Server & Webhook Subsystem.
"""

import asyncio
from pathlib import Path
import tempfile
import pytest
from fastapi.testclient import TestClient

from scandoc.cli import main
from scandoc.cli.taxonomy import ExitCode
from scandoc.server import ServerConfig, create_app
from scandoc.server.routes.convert import sanitize_filename
from scandoc.server.taxonomy import JobStatus, ServerErrorCode
from scandoc.server.webhooks import WebhookDispatcher
from fixtures.pdf_fixtures import generate_digital_pdf_bytes


@pytest.fixture
def test_app():
    cfg = ServerConfig(max_upload_bytes=1048576, webhook_secret="test_webhook_secret_key_123")
    return create_app(cfg)


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


@pytest.fixture
def pdf_bytes():
    return generate_digital_pdf_bytes(text="REST API Test Document Content")


# 1. Health, Readiness, and OpenAPI Tests
def test_health_and_readiness(client):
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json() == {"status": "ok"}

    res_ready = client.get("/ready")
    assert res_ready.status_code == 200
    data_ready = res_ready.json()
    assert data_ready["status"] == "ready"
    assert "active_device" in data_ready


def test_openapi_schema(client):
    res = client.get("/openapi.json")
    assert res.status_code == 200
    data = res.json()
    assert data["info"]["title"] == "scanDOC Document Intelligence Engine REST API"
    assert "/health" in data["paths"]
    assert "/api/v1/convert" in data["paths"]
    assert "/api/v1/jobs" in data["paths"]


# 2. Filename Sanitization & Path Traversal Security Tests
def test_filename_sanitization():
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("C:\\Windows\\System32\\cmd.exe") == "cmd.exe"
    assert sanitize_filename("my_doc.pdf") == "my_doc.pdf"


# 3. Synchronous Conversion Endpoint Tests
def test_sync_convert_success(client, pdf_bytes):
    files = {"file": ("test_doc.pdf", pdf_bytes, "application/pdf")}
    data = {"format": "markdown"}
    res = client.post("/api/v1/convert", files=files, data=data)
    assert res.status_code == 200
    assert "REST API Test Document Content" in res.text


def test_sync_convert_invalid_format(client, pdf_bytes):
    files = {"file": ("test_doc.pdf", pdf_bytes, "application/pdf")}
    data = {"format": "unsupported_fmt_xyz"}
    res = client.post("/api/v1/convert", files=files, data=data)
    assert res.status_code == 400
    err = res.json()["detail"]
    assert err["error_code"] == ServerErrorCode.UNSUPPORTED_FORMAT.value


def test_sync_convert_payload_too_large(pdf_bytes):
    cfg = ServerConfig(max_upload_bytes=10)  # Very small limit
    small_app = create_app(cfg)
    small_client = TestClient(small_app)

    files = {"file": ("test_doc.pdf", pdf_bytes, "application/pdf")}
    res = small_client.post("/api/v1/convert", files=files)
    assert res.status_code == 413
    assert res.json()["detail"]["error_code"] == ServerErrorCode.PAYLOAD_TOO_LARGE.value


# 4. Asynchronous Jobs Lifecycle Tests (Create, Status, Result, Cancel)
def test_async_job_lifecycle(client, pdf_bytes):
    # 1. Create Job
    files = {"file": ("async_doc.pdf", pdf_bytes, "application/pdf")}
    data = {"format": "markdown"}
    res_create = client.post("/api/v1/jobs", files=files, data=data)
    assert res_create.status_code == 202
    job_info = res_create.json()
    job_id = job_info["job_id"]
    assert job_info["status"] in [JobStatus.QUEUED.value, JobStatus.RUNNING.value]

    # 2. Wait for completion
    completed = False
    for _ in range(50):
        res_stat = client.get(f"/api/v1/jobs/{job_id}")
        assert res_stat.status_code == 200
        stat_data = res_stat.json()
        if stat_data["status"] == JobStatus.COMPLETED.value:
            completed = True
            break
        elif stat_data["status"] == JobStatus.FAILED.value:
            pytest.fail(f"Job failed: {stat_data.get('error_message')}")
        import time
        time.sleep(0.1)

    assert completed is True

    # 3. Retrieve Result
    res_result = client.get(f"/api/v1/jobs/{job_id}/result")
    assert res_result.status_code == 200
    assert "REST API Test Document Content" in res_result.text


def test_async_job_cancellation(client, pdf_bytes):
    files = {"file": ("cancel_doc.pdf", pdf_bytes, "application/pdf")}
    res_create = client.post("/api/v1/jobs", files=files)
    job_id = res_create.json()["job_id"]

    res_cancel = client.post(f"/api/v1/jobs/{job_id}/cancel")
    assert res_cancel.status_code in [200, 400]
    res_stat = client.get(f"/api/v1/jobs/{job_id}")
    assert res_stat.json()["status"] in [JobStatus.CANCELLED.value, JobStatus.COMPLETED.value, JobStatus.RUNNING.value]


def test_job_not_found_404(client):
    res = client.get("/api/v1/jobs/non_existent_job_123")
    assert res.status_code == 404
    assert res.json()["detail"]["error_code"] == ServerErrorCode.NOT_FOUND.value


# 5. Telemetry & Observability Test
def test_telemetry_endpoint(client):
    res = client.get("/api/v1/telemetry")
    assert res.status_code == 200
    data = res.json()
    assert "telemetry" in data
    assert "total_jobs" in data["telemetry"]


# 6. Webhook Dispatcher & HMAC Signature Tests
@pytest.mark.asyncio
async def test_webhook_hmac_signature_and_dispatch():
    secret = "my_secure_webhook_secret_key"
    dispatcher = WebhookDispatcher(secret=secret, timeout_sec=2.0, max_retries=1)

    payload = b'{"event_id": "123", "status": "completed"}'
    sig = dispatcher.compute_signature(payload)
    assert sig is not None
    assert sig.startswith("sha256=")

    # Test delivery failure handles gracefully without crashing
    success = await dispatcher.dispatch_job_event(
        webhook_url="http://127.0.0.1:59999/non_existent_webhook",
        job_id="job_test_123",
        status=JobStatus.COMPLETED,
    )
    assert success is False


# 7. CLI Command `scandoc serve` Test
def test_cli_serve_subcommand():
    ret = main(["serve", "--port", "8999", "--json"])
    assert ret == ExitCode.SUCCESS
