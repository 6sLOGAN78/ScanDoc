"""
ProviderFactory constructing validated provider instances.
"""

import logging
from typing import Any, Dict, Optional, Type

from scandoc.providers.ecosystem.credentials import CredentialReference
from scandoc.providers.ecosystem.exceptions import ProviderValidationError
from scandoc.providers.ecosystem.models import ProviderDescriptor
from scandoc.providers.ecosystem.taxonomy import ProviderHealthState
from scandoc.providers.ecosystem.validator import ProviderValidator

logger = logging.getLogger("scandoc.providers.ecosystem.factory")


class ProviderFactory:
    """
    Factory for safe instantiation of document processing providers.
    Prevents unvalidated initialization.
    """

    @classmethod
    def create_provider(
        cls,
        provider_cls: Type[Any],
        descriptor: ProviderDescriptor,
        config: Optional[Dict[str, Any]] = None,
        credential_ref: Optional[CredentialReference] = None,
    ) -> Any:
        """
        Validate provider pre-flight requirements and construct instance.
        """
        health = ProviderValidator.validate_provider(descriptor, config, credential_ref)
        if health.state != ProviderHealthState.AVAILABLE:
            raise ProviderValidationError(
                f"Cannot create provider '{descriptor.provider_id}': {health.details}"
            )

        logger.info("Instantiating provider '%s' (Type: %s)", descriptor.provider_id, descriptor.provider_type.value)
        return provider_cls()
