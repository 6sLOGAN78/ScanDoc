"""
ModelStore abstraction managing local model directories, metadata, size calculation, and SHA-256 verification.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import List, Optional

from scandoc.models_mgmt.models import ModelSpec
from scandoc.models_mgmt.taxonomy import ModelState, TaskType

logger = logging.getLogger("scandoc.models_mgmt.store")

import os
DEFAULT_MODEL_DIR = Path(os.environ.get("SCANDOC_MODELS_DIR", Path.home() / "local" / "scandoc" / "models"))

class ModelStore:
    """
    Manages local model directory hierarchy (~/.scandoc/models/), metadata persistence,
    file verification, and disk storage calculations.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self._base_dir = Path(base_dir or DEFAULT_MODEL_DIR).expanduser().resolve()
        self._ensure_directories()

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    def _ensure_directories(self) -> None:
        """Create task-specific subdirectories if missing."""
        for task in TaskType:
            sub = self._base_dir / task.value
            sub.mkdir(parents=True, exist_ok=True)

    def determine_path(self, spec: ModelSpec) -> Path:
        """Determine local storage path for a model specification."""
        task_dir = self._base_dir / spec.task.value
        # Sanitize model_id for directory path
        clean_name = spec.model_id.replace("/", "_").replace(":", "_")
        return task_dir / clean_name

    def write_metadata(self, spec: ModelSpec) -> Path:
        """Write model specification metadata JSON file in model directory."""
        model_dir = self.determine_path(spec)
        model_dir.mkdir(parents=True, exist_ok=True)
        meta_file = model_dir / "model_spec.json"
        
        updated_spec = spec.model_copy(update={"local_path": str(model_dir)})
        meta_file.write_text(updated_spec.model_dump_json(indent=2), encoding="utf-8")
        return meta_file

    def get_model_spec(self, model_id: str) -> Optional[ModelSpec]:
        """Read model specification metadata for a given model ID."""
        for task in TaskType:
            clean_name = model_id.replace("/", "_").replace(":", "_")
            meta_file = self._base_dir / task.value / clean_name / "model_spec.json"
            if meta_file.exists():
                try:
                    data = json.loads(meta_file.read_text(encoding="utf-8"))
                    return ModelSpec(**data)
                except Exception as e:
                    logger.warning("Failed to parse metadata file '%s': %s", meta_file, e)
        return None

    def list_installed_models(self) -> List[ModelSpec]:
        """List all installed models across all task subdirectories."""
        installed: List[ModelSpec] = []
        for task in TaskType:
            task_dir = self._base_dir / task.value
            if not task_dir.exists():
                continue
            for model_dir in task_dir.iterdir():
                if model_dir.is_dir():
                    meta_file = model_dir / "model_spec.json"
                    if meta_file.exists():
                        try:
                            data = json.loads(meta_file.read_text(encoding="utf-8"))
                            installed.append(ModelSpec(**data))
                        except Exception as e:
                            logger.warning("Skipping corrupted metadata in '%s': %s", meta_file, e)
        return installed

    def delete_model(self, model_id: str) -> bool:
        """Delete local model directory and metadata."""
        spec = self.get_model_spec(model_id)
        if spec and spec.local_path:
            p = Path(spec.local_path)
            if p.exists():
                import shutil
                shutil.rmtree(p)
                return True
        return False

    @classmethod
    def calculate_size(cls, path: Path) -> int:
        """Calculate total directory or file size in bytes."""
        if not path.exists():
            return 0
        if path.is_file():
            return path.stat().st_size
        return sum(f.stat().st_size for f in path.glob("**/*") if f.is_file())

    @classmethod
    def verify_checksum(cls, path: Path, expected_sha256: str) -> bool:
        """Verify SHA-256 cryptographic checksum of a file."""
        if not path.exists() or not path.is_file():
            return False
        hasher = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        calculated = hasher.hexdigest().lower()
        return calculated == expected_sha256.lower()
