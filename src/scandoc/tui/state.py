"""
Reactive Application State model for scanDOC TUI.
"""

from dataclasses import dataclass, field
from pathlib import Path
import os
from typing import Any, Dict, List, Optional

from scandoc.acceleration.models import DeviceType, PrecisionMode
from scandoc.models.document import DocumentIR
from scandoc.pipelines.models import PipelineConfig


class ScreenType:
    HOME = "home"
    FILE_PICKER = "file_picker"
    FOLDER_PICKER = "folder_picker"
    PIPELINE_CONFIG = "pipeline_config"
    PROCESSING = "processing"
    DOCUMENT_INSPECTOR = "document_inspector"
    EXPORT = "export"
    MODEL_MANAGER = "model_manager"
    BENCHMARK = "benchmark"
    SERVER_MANAGER = "server_manager"
    SETTINGS = "settings"
    HELP = "help"
    COMMAND_PALETTE = "command_palette"


@dataclass
class TuiState:
    """State tree for scanDOC TUI interface."""
    current_screen: str = ScreenType.HOME
    previous_screen: Optional[str] = None
    
    # File Navigation & Selection State
    current_dir: Path = field(default_factory=lambda: Path.cwd())
    selected_paths: List[Path] = field(default_factory=list)
    search_query: str = ""
    extension_filter: Optional[str] = None
    
    # Active Processing Document State
    active_document_ir: Optional[DocumentIR] = None
    active_document_path: Optional[Path] = None
    processing_status: str = "idle"  # 'idle', 'processing', 'completed', 'failed', 'cancelled'
    progress_stage: str = "Ready"
    progress_pct: float = 0.0
    current_page: int = 0
    total_pages: int = 0
    processing_errors: List[str] = field(default_factory=list)
    processing_logs: List[str] = field(default_factory=list)
    
    # Pipeline & Device Config
    pipeline_config: PipelineConfig = field(default_factory=PipelineConfig)
    offline_mode: bool = field(default_factory=lambda: os.getenv("SCANDOC_OFFLINE", "0") == "1")
    device_type: DeviceType = DeviceType.CPU
    precision_mode: PrecisionMode = PrecisionMode.FP32
    
    # Export Options
    selected_export_format: str = "markdown"
    export_output_dir: Path = field(default_factory=lambda: Path.cwd() / "output")
    include_images: bool = True
    preserve_formulas: bool = True
    preserve_tables: bool = True
    
    # Server State
    server_running: bool = False
    server_host: str = "127.0.0.1"
    server_port: int = 8000
    
    # Recent Documents History
    recent_documents: List[Dict[str, Any]] = field(default_factory=list)

    def is_offline(self) -> bool:
        return self.offline_mode or os.getenv("SCANDOC_OFFLINE", "0") == "1"

    def toggle_offline_mode(self) -> bool:
        self.offline_mode = not self.offline_mode
        os.environ["SCANDOC_OFFLINE"] = "1" if self.offline_mode else "0"
        return self.offline_mode

    def add_log(self, message: str) -> None:
        self.processing_logs.append(message)
        if len(self.processing_logs) > 500:
            self.processing_logs.pop(0)

    def add_recent(self, path: Path, status: str = "completed") -> None:
        rec = {
            "name": path.name,
            "path": str(path.resolve()),
            "status": status,
            "size_bytes": path.stat().st_size if path.exists() else 0,
        }
        self.recent_documents = [r for r in self.recent_documents if r["path"] != rec["path"]]
        self.recent_documents.insert(0, rec)
        self.recent_documents = self.recent_documents[:20]
