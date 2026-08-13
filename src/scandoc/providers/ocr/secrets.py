"""
Secure secret reference container preventing raw API keys from leaking into logs, IR, or Git.
"""

import json
import os
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_serializer


class SecretRef(BaseModel):
    """
    Secure secret reference container.
    
    References secrets via environment variable names or explicit masked strings.
    Guarantees that raw secret values are NEVER printed in __repr__, __str__, or serialized dicts.
    """
    env_var: Optional[str] = Field(None, description="Environment variable name holding secret (e.g., 'OPENAI_API_KEY')")
    raw_secret_value: Optional[str] = Field(None, description="Raw secret string value")

    @field_serializer("raw_secret_value")
    def serialize_raw_secret(self, raw_secret_value: Optional[str]) -> Optional[str]:
        """Automatically redact raw secret value during Pydantic dict / JSON serialization."""
        if raw_secret_value is not None:
            return "***REDACTED***"
        return None

    def get_secret_value(self) -> Optional[str]:
        """
        Retrieve raw secret string value.
        
        Reads from environment variable if env_var is specified,
        otherwise returns raw_secret_value if provided.
        """
        if self.env_var:
            return os.getenv(self.env_var)
        return self.raw_secret_value

    def __repr__(self) -> str:
        if self.env_var:
            return f"SecretRef(env_var='{self.env_var}')"
        return "SecretRef(raw_secret_value='***REDACTED***')"

    def __str__(self) -> str:
        return repr(self)
