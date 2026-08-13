"""
CredentialReference abstraction preventing raw secret leaks in logs, plans, and metadata.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field, field_serializer


class CredentialReference(BaseModel):
    """
    Reference to credentials resolved at runtime without storing raw secrets.
    """
    credential_id: str = Field(..., description="Unique credential reference ID")
    source_type: str = Field("env", description="Credential source ('env', 'system')")
    env_var_name: Optional[str] = Field(None, description="Environment variable name storing secret")

    @field_serializer("env_var_name")
    def serialize_env_var(self, env_var_name: Optional[str], _info) -> Optional[str]:
        # Always preserve variable name in references, but never expose raw contents
        return env_var_name

    def resolve_value(self) -> Optional[str]:
        """
        Safely resolve raw secret value from runtime environment.
        """
        if self.source_type == "env" and self.env_var_name:
            return os.environ.get(self.env_var_name)
        return None

    def __repr__(self) -> str:
        return f"CredentialReference(id='{self.credential_id}', source='{self.source_type}')"

    def __str__(self) -> str:
        return f"CredentialReference({self.credential_id})"
