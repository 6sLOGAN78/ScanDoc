"""
Provider-independent VLM structured output validation engine.
"""

import json
import logging
from typing import Any, Dict, List

from scandoc.providers.vlm.exceptions import VlmOutputValidationError

logger = logging.getLogger("scandoc.providers.vlm.validator")


class VlmOutputValidator:
    """
    Validates VLM output text, ensures JSON syntax compliance, and verifies required schema fields.
    """

    @classmethod
    def validate_json(cls, raw_text: str) -> Dict[str, Any]:
        """
        Parse and validate JSON string output from VLM.
        Raises VlmOutputValidationError if raw_text is malformed or unparseable.
        """
        if not raw_text or not raw_text.strip():
            raise VlmOutputValidationError("VLM output string is empty.")

        clean_text = raw_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        try:
            parsed = json.loads(clean_text)
            if not isinstance(parsed, dict):
                raise VlmOutputValidationError(f"Expected VLM JSON object dict, got {type(parsed).__name__}")
            return parsed
        except json.JSONDecodeError as e:
            raise VlmOutputValidationError(f"Malformed VLM JSON output: {e}") from e

    @classmethod
    def validate_schema(cls, data: Dict[str, Any], required_keys: List[str]) -> bool:
        """
        Verify that structured output dictionary contains all required schema keys.
        """
        missing = [key for key in required_keys if key not in data]
        if missing:
            raise VlmOutputValidationError(f"VLM JSON output is missing required keys: {missing}")
        return True
