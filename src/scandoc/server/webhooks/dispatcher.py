"""
Webhook dispatcher with HMAC-SHA256 signing, async delivery, retries, and idempotency.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
import uuid
from typing import Optional

import httpx

from scandoc.server.models import WebhookPayload
from scandoc.server.taxonomy import JobStatus, WebhookEventType

logger = logging.getLogger("scandoc.server.webhooks")


class WebhookDispatcher:
    """
    Handles secure, asynchronous webhook event delivery.
    """

    def __init__(
        self,
        secret: Optional[str] = None,
        timeout_sec: float = 5.0,
        max_retries: int = 3,
    ):
        self.secret = secret
        self.timeout_sec = timeout_sec
        self.max_retries = max_retries

    def compute_signature(self, payload_bytes: bytes) -> Optional[str]:
        """Compute HMAC-SHA256 hex signature if a secret is configured."""
        if not self.secret:
            return None
        sig = hmac.new(self.secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
        return f"sha256={sig}"

    async def dispatch_job_event(
        self,
        webhook_url: str,
        job_id: str,
        status: JobStatus,
        result_url: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Build and deliver signed webhook notification to target endpoint with retry logic.
        """
        if not webhook_url:
            return False

        # Map JobStatus to WebhookEventType
        event_map = {
            JobStatus.COMPLETED: WebhookEventType.JOB_COMPLETED,
            JobStatus.FAILED: WebhookEventType.JOB_FAILED,
            JobStatus.CANCELLED: WebhookEventType.JOB_CANCELLED,
        }
        event_type = event_map.get(status, WebhookEventType.JOB_COMPLETED)

        payload = WebhookPayload(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            job_id=job_id,
            status=status,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            result_url=result_url,
            error_message=error_message,
        )

        payload_bytes = payload.model_dump_json().encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "scanDOC-WebhookDispatcher/1.0",
            "X-ScanDoc-Event": event_type.value,
            "X-ScanDoc-Event-ID": payload.event_id,
        }

        signature = self.compute_signature(payload_bytes)
        if signature:
            headers["X-ScanDoc-Signature"] = signature

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                    resp = await client.post(webhook_url, content=payload_bytes, headers=headers)
                    if 200 <= resp.status_code < 300:
                        logger.info(f"Webhook delivered successfully to {webhook_url} (attempt {attempt})")
                        return True
                    else:
                        logger.warning(f"Webhook delivery failed HTTP {resp.status_code} to {webhook_url} (attempt {attempt})")
            except Exception as exc:
                logger.warning(f"Webhook exception on delivery to {webhook_url} (attempt {attempt}): {exc}")

            if attempt < self.max_retries:
                await asyncio.sleep(0.2 * (2 ** (attempt - 1)))  # Exponential backoff

        return False
