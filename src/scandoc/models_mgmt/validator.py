"""
ModelValidator engine verifying file existence, SHA-256 checksums, and hardware compatibility.
"""

import logging
from pathlib import Path

from scandoc.acceleration.manager import default_execution_manager
from scandoc.models_mgmt.models import ModelSpec, ValidationResult
from scandoc.models_mgmt.store import ModelStore

logger = logging.getLogger("scandoc.models_mgmt.validator")


class ModelValidator:
    """
    Validates model artifact completeness, cryptographic checksums, and hardware runtime compatibility.
    """

    @classmethod
    def validate(cls, spec: ModelSpec, store: ModelStore) -> ValidationResult:
        errors = []
        checksum_verified = False
        hardware_compatible = True

        # Check local path existence
        if not spec.local_path:
            errors.append(f"Model '{spec.model_id}' has no local_path specified.")
            return ValidationResult(is_valid=False, errors=errors, checksum_verified=False, hardware_compatible=False)

        model_path = Path(spec.local_path)
        if not model_path.exists():
            errors.append(f"Model path does not exist: {model_path}")
            return ValidationResult(is_valid=False, errors=errors, checksum_verified=False, hardware_compatible=False)

        # Check SHA-256 checksum if specified
        if spec.checksum_sha256:
            target_file = model_path
            if model_path.is_dir():
                # Locate primary weights file
                weights_files = list(model_path.glob("*.onnx")) or list(model_path.glob("*.bin")) or list(model_path.glob("*.safetensors"))
                if weights_files:
                    target_file = weights_files[0]

            if store.verify_checksum(target_file, spec.checksum_sha256):
                checksum_verified = True
            else:
                errors.append(f"SHA-256 checksum verification failed for '{target_file}'")

        # Check hardware compatibility via DeviceDiscovery
        from scandoc.acceleration.discovery import DeviceDiscovery
        available_devices = DeviceDiscovery.discover_devices()
        dev_strings = [d.to_device_string().lower() for d in available_devices]

        if spec.supported_devices:
            supported_lower = [dev.lower() for dev in spec.supported_devices]
            # Check if at least CPU or any requested device is available
            compatible = any(dev in dev_strings or dev == "cpu" for dev in supported_lower)
            if not compatible:
                hardware_compatible = False
                errors.append(f"No compatible hardware execution backend available for devices: {spec.supported_devices}")

        is_valid = (len(errors) == 0)
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            checksum_verified=checksum_verified,
            hardware_compatible=hardware_compatible,
        )
