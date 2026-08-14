# scanDOC REST API Server Guide

## 1. Overview & Architecture

The scanDOC REST API server (`scandoc.server`) exposes the scanDOC Document Intelligence Engine over HTTP using FastAPI and Uvicorn. It supports both synchronous document conversion and asynchronous job processing with webhook notifications, HMAC signatures, and clean secret redaction.

---

## 2. Starting the Server

Start the API server via CLI:
```bash
scandoc serve --host 127.0.0.1 --port 8000 --workers 4
```

Interactive OpenAPI documentation is automatically available at:
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`
- **OpenAPI Schema**: `http://127.0.0.1:8000/openapi.json`

---

## 3. Core API Endpoints & Curl Examples

### Health Check (Liveness)
```bash
curl -X GET "http://127.0.0.1:8000/health"
```
**Response (200 OK)**:
```json
{
  "status": "ok"
}
```

### Readiness Check
```bash
curl -X GET "http://127.0.0.1:8000/ready"
```
**Response (200 OK)**:
```json
{
  "status": "ready",
  "engine": "scanDOC Document Intelligence Engine",
  "active_device": "cpu"
}
```

---

### Synchronous Conversion (`POST /api/v1/convert`)
For quick, direct document conversion:
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/convert" \
  -F "file=@document.pdf" \
  -F "format=markdown"
```

---

### Asynchronous Processing (`POST /api/v1/jobs`)
For background processing of complex or multi-page documents:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/jobs" \
  -F "file=@large_document.pdf" \
  -F "format=markdown" \
  -F "webhook_url=https://example.com/api/webhook"
```
**Response (202 Accepted)**:
```json
{
  "job_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "queued",
  "created_at": "2026-08-14T17:00:00Z",
  "message": "Job successfully queued for background processing."
}
```

---

### Job Progress & Status (`GET /api/v1/jobs/{job_id}`)
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/jobs/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
```
**Response (200 OK)**:
```json
{
  "job_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "completed",
  "file_name": "large_document.pdf",
  "format": "markdown",
  "progress": {
    "pages_processed": 5,
    "total_pages": 5,
    "percentage": 100.0,
    "current_stage": "completed",
    "elapsed_sec": 1.24
  },
  "created_at": "2026-08-14T17:00:00Z",
  "completed_at": "2026-08-14T17:00:01Z"
}
```

---

### Retrieve Job Result (`GET /api/v1/jobs/{job_id}/result`)
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/jobs/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d/result"
```

---

### Job Cancellation (`POST /api/v1/jobs/{job_id}/cancel`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/jobs/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d/cancel"
```

---

## 4. Webhooks & HMAC Verification

When configured with a `webhook_url`, scanDOC dispatches an HTTP POST request upon job completion, failure, or cancellation.

### Webhook Headers:
- `Content-Type`: `application/json`
- `X-ScanDoc-Event`: `job.completed` | `job.failed` | `job.cancelled`
- `X-ScanDoc-Event-ID`: Unique UUID4 event identifier (for consumer deduplication)
- `X-ScanDoc-Signature`: `sha256=<hex_digest>` computed using HMAC-SHA256 over raw payload bytes.

### Signature Verification Code (Python Example):
```python
import hmac
import hashlib

def verify_webhook(raw_payload: bytes, signature_header: str, secret: str) -> bool:
    expected_sig = "sha256=" + hmac.new(secret.encode(), raw_payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_sig, signature_header)
```
