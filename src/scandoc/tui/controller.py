"""
TUI Application Controller orchestrating scanDOC backend services.
"""

from concurrent.futures import ThreadPoolExecutor
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from scandoc.acceleration import ExecutionManager, default_execution_manager
from scandoc.benchmarks import BenchmarkConfig, BenchmarkRunner
from scandoc.exporters import ExportOptions, default_exporter_registry
from scandoc.models_mgmt import default_model_manager
from scandoc.pipelines import DocumentPipeline, PipelineConfig
from scandoc.providers.ecosystem.registry import default_provider_registry
from scandoc.server import ServerConfig, create_app
from scandoc.tui.state import ScreenType, TuiState

logger = logging.getLogger("scandoc.tui.controller")


class TuiController:
    """
    Controller connecting TUI state and actions directly to existing scanDOC backend services.
    Ensures ZERO business logic duplication inside the UI layer.
    """

    def __init__(self, state: Optional[TuiState] = None):
        self.state = state or TuiState()
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._server_app: Optional[Any] = None

    # Navigation Actions
    def navigate_to(self, screen: str) -> None:
        self.state.previous_screen = self.state.current_screen
        self.state.current_screen = screen

    def navigate_back(self) -> None:
        if self.state.previous_screen:
            self.state.current_screen, self.state.previous_screen = self.state.previous_screen, None
        else:
            self.state.current_screen = ScreenType.HOME

    # File & Directory Operations
    def list_directory_files(self, directory: Optional[Path] = None) -> List[Tuple[Path, bool, int, str]]:
        """
        List contents of target directory with (path, is_dir, size_bytes, format_desc).
        """
        target_dir = (directory or self.state.current_dir).resolve()
        if not target_dir.exists() or not target_dir.is_dir():
            target_dir = Path.cwd()
        self.state.current_dir = target_dir

        results = []
        try:
            for item in sorted(target_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                if item.name.startswith("."):
                    continue
                if self.state.search_query and self.state.search_query.lower() not in item.name.lower():
                    continue

                if item.is_dir():
                    results.append((item, True, 0, "Folder"))
                else:
                    ext = item.suffix.lower()
                    if self.state.extension_filter and ext != self.state.extension_filter.lower():
                        continue
                    size = item.stat().st_size if item.exists() else 0
                    results.append((item, False, size, ext[1:].upper() if ext else "FILE"))
        except Exception as e:
            logger.error("Failed to list directory '%s': %s", target_dir, e)
            self.state.add_log(f"Error reading directory: {e}")

        return results

    # Document Processing Actions
    def process_selected_documents(self) -> None:
        """Process currently selected file or directory using DocumentPipeline."""
        if not self.state.selected_paths:
            self.state.add_log("No documents selected to process.")
            return

        self.state.processing_status = "processing"
        self.state.progress_stage = "Starting Pipeline"
        self.state.progress_pct = 0.0
        self.navigate_to(ScreenType.PROCESSING)

        self._executor.submit(self._run_processing_task)

    def _run_processing_task(self) -> None:
        try:
            paths = list(self.state.selected_paths)
            total = len(paths)
            pipeline = DocumentPipeline(config=self.state.pipeline_config)

            for idx, path in enumerate(paths, start=1):
                self.state.progress_stage = f"Processing ({idx}/{total}): {path.name}"
                self.state.progress_pct = (idx - 1) / max(1, total) * 100.0
                self.state.add_log(f"Starting processing for '{path.name}'")

                res = pipeline.process(path)
                if res.status == "success" and res.document_ir:
                    self.state.active_document_ir = res.document_ir
                    self.state.active_document_path = path
                    self.state.add_recent(path, status="success")
                    self.state.add_log(f"Successfully processed '{path.name}' ({len(res.document_ir.pages)} pages)")
                else:
                    err_msg = "; ".join(res.errors) if res.errors else "Unknown processing failure"
                    self.state.processing_errors.append(f"{path.name}: {err_msg}")
                    self.state.add_log(f"Error processing '{path.name}': {err_msg}")

            self.state.progress_pct = 100.0
            self.state.progress_stage = "Processing Completed"
            self.state.processing_status = "completed"

        except Exception as e:
            logger.error("Pipeline task failed: %s", e)
            self.state.processing_status = "failed"
            self.state.processing_errors.append(str(e))
            self.state.add_log(f"Pipeline error: {e}")

    # Model Manager Actions
    def list_models_status(self) -> List[Dict[str, Any]]:
        """Return list of models with install and cache status from ModelManager."""
        results = []
        for m in default_model_manager.list_available_models():
            installed = default_model_manager.is_installed(m.model_id)
            results.append({
                "model_id": m.model_id,
                "name": m.model_name,
                "exists": installed,
                "size_bytes": m.size_bytes or 15000000,
            })
        return results

    def download_model(self, model_id: str) -> bool:
        """Download model via Phase 34 ModelManager with offline check."""
        if self.state.is_offline():
            self.state.add_log(f"Cannot download model '{model_id}' while in Offline Mode.")
            return False

        try:
            self.state.add_log(f"Downloading model '{model_id}'...")
            res = default_model_manager.download_model(model_id)
            self.state.add_log(f"Model '{model_id}' downloaded to {res.installed_path}")
            return True
        except Exception as e:
            self.state.add_log(f"Download failed for '{model_id}': {e}")
            return False

    def clear_model_cache(self, model_id: str) -> bool:
        """Clear model cache via ModelManager."""
        try:
            default_model_manager.clear_cache(model_id)
            self.state.add_log(f"Cleared cache for model '{model_id}'.")
            return True
        except Exception as e:
            self.state.add_log(f"Failed to clear cache for '{model_id}': {e}")
            return False

    # Export Actions
    def export_active_document(self, format_id: str) -> Optional[Path]:
        """Export active DocumentIR using ExporterRegistry."""
        if not self.state.active_document_ir:
            self.state.add_log("No active document available for export.")
            return None

        try:
            opt = ExportOptions(
                format_id=format_id,
                output_dir=self.state.export_output_dir,
                include_images=self.state.include_images,
                preserve_formulas=self.state.preserve_formulas,
                preserve_tables=self.state.preserve_tables,
            )
            export_res = default_exporter_registry.export(self.state.active_document_ir, options=opt)
            
            # Write to disk
            self.state.export_output_dir.mkdir(parents=True, exist_ok=True)
            stem = self.state.active_document_path.stem if self.state.active_document_path else "exported_doc"
            ext = f".{format_id}" if not format_id.startswith("rag") else ".json"
            out_file = self.state.export_output_dir / f"{stem}{ext}"

            if isinstance(export_res.content, bytes):
                out_file.write_bytes(export_res.content)
            else:
                out_file.write_text(str(export_res.content), encoding="utf-8")

            self.state.add_log(f"Exported document to '{out_file}' in '{format_id}' format.")
            return out_file

        except Exception as e:
            logger.error("Export failed: %s", e)
            self.state.add_log(f"Export failed: {e}")
            return None

    # Benchmark Actions
    def run_benchmark_suite(self) -> Dict[str, Any]:
        """Run Phase 33 Benchmark suite using BenchmarkRunner."""
        try:
            self.state.add_log("Running scanDOC vs Docling benchmark suite...")
            runner = BenchmarkRunner(config=BenchmarkConfig(warmup_runs=1, benchmark_rounds=3))
            report = runner.run_benchmarks()
            self.state.add_log("Benchmark suite completed successfully.")
            return report.to_dict()
        except Exception as e:
            self.state.add_log(f"Benchmark error: {e}")
            return {"error": str(e)}

    # Server Control Actions
    def start_server(self, host: str = "127.0.0.1", port: int = 8000) -> bool:
        """Start REST API & Studio server using create_app."""
        try:
            self.state.server_host = host
            self.state.server_port = port
            cfg = ServerConfig(host=host, port=port)
            self._server_app = create_app(cfg)
            self.state.server_running = True
            self.state.add_log(f"REST & Studio server initialized on http://{host}:{port}")
            return True
        except Exception as e:
            self.state.add_log(f"Failed to start server: {e}")
            return False

    def stop_server(self) -> None:
        self.state.server_running = False
        self._server_app = None
        self.state.add_log("REST server stopped.")
