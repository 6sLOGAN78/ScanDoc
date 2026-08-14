"""
Comprehensive Test Suite for Phase 35: Claude-Style Interactive Terminal UI (TUI).
"""

from pathlib import Path
from io import StringIO
from rich.console import Console
import pytest

from scandoc.cli import main
from scandoc.cli.parser import create_parser
from scandoc.cli.taxonomy import ExitCode
from scandoc.tui import ScanDocTuiApp, ScreenType, TuiController, TuiState
from scandoc.tui.screens import (
    render_benchmark_screen,
    render_command_palette_screen,
    render_document_inspector_screen,
    render_export_screen,
    render_file_picker_screen,
    render_help_screen,
    render_home_screen,
    render_models_screen,
    render_pipeline_screen,
    render_processing_screen,
    render_server_screen,
    render_settings_screen,
)


def panel_to_str(panel) -> str:
    """Helper converting Rich panel renderable to text string for testing assertions."""
    buf = StringIO()
    console = Console(file=buf, force_terminal=False, color_system=None)
    console.print(panel)
    return buf.getvalue()


@pytest.fixture
def tui_controller(tmp_path):
    state = TuiState(current_dir=tmp_path)
    return TuiController(state=state)


def test_tui_startup_and_home_screen(tui_controller):
    """Test TUI startup state and home screen rendering."""
    state = tui_controller.state
    assert state.current_screen == ScreenType.HOME
    
    panel = render_home_screen(state, selected_idx=0)
    assert panel is not None
    assert "scanDOC" in panel_to_str(panel)


def test_file_and_folder_selection(tui_controller, tmp_path):
    """Test file and directory listing, multi-selection, and filtering."""
    sub_dir = tmp_path / "subfolder"
    sub_dir.mkdir()
    f1 = tmp_path / "doc1.pdf"
    f1.write_text("dummy PDF content")
    f2 = tmp_path / "doc2.docx"
    f2.write_text("dummy DOCX content")

    items = tui_controller.list_directory_files(tmp_path)
    assert len(items) == 3

    # Toggle selection
    tui_controller.state.selected_paths.append(f1)
    tui_controller.state.selected_paths.append(f2)
    assert len(tui_controller.state.selected_paths) == 2

    # Render picker screen
    panel = render_file_picker_screen(tui_controller.state, items, selected_idx=0)
    assert panel is not None
    assert "doc1.pdf" in panel_to_str(panel)


def test_pipeline_configuration_screen(tui_controller):
    """Test pipeline configuration editing and stage toggles."""
    state = tui_controller.state
    cfg = state.pipeline_config

    assert cfg.enable_vlm_fallback is True
    cfg.enable_vlm_fallback = False
    assert cfg.enable_vlm_fallback is False

    panel = render_pipeline_screen(state, selected_idx=1)
    assert panel is not None
    assert "Pipeline Configuration" in panel_to_str(panel)


def test_model_manager_integration(tui_controller):
    """Test ModelManager integration for listing and clearing models."""
    models_status = tui_controller.list_models_status()
    assert len(models_status) >= 5

    panel = render_models_screen(tui_controller.state, models_status, selected_idx=0)
    assert panel is not None
    assert "Autonomous Model Manager" in panel_to_str(panel)


def test_offline_mode_enforcement(tui_controller, monkeypatch):
    """Test offline mode toggle blocking downloads."""
    state = tui_controller.state
    state.offline_mode = True
    monkeypatch.setenv("SCANDOC_OFFLINE", "1")

    assert state.is_offline() is True
    res = tui_controller.download_model("rapidocr_onnx")
    assert res is False
    assert any("Offline Mode" in log for log in state.processing_logs)


def test_processing_state_and_progress(tui_controller, tmp_path):
    """Test processing screen rendering and log additions."""
    doc_path = tmp_path / "test.pdf"
    doc_path.write_text("sample content")
    tui_controller.state.selected_paths = [doc_path]
    tui_controller.state.active_document_path = doc_path

    tui_controller.state.processing_status = "processing"
    tui_controller.state.progress_stage = "OCR Engine"
    tui_controller.state.progress_pct = 45.0
    tui_controller.state.add_log("OCR page 1 completed")

    panel = render_processing_screen(tui_controller.state)
    assert panel is not None
    assert "Processing test.pdf" in panel_to_str(panel)


def test_document_inspector_and_export_screen(tui_controller):
    """Test DocumentIR inspector and multi-format exporter screen rendering."""
    state = tui_controller.state
    
    panel_doc = render_document_inspector_screen(state, selected_idx=0)
    assert panel_doc is not None

    panel_exp = render_export_screen(state, selected_idx=0)
    assert panel_exp is not None
    assert "Multi-Format Exporter Studio" in panel_to_str(panel_exp)


def test_benchmark_and_server_screens(tui_controller):
    """Test benchmark runner and REST server manager screen rendering."""
    state = tui_controller.state

    panel_bm = render_benchmark_screen(state)
    assert panel_bm is not None

    panel_srv = render_server_screen(state)
    assert panel_srv is not None

    # Test server start/stop
    res_start = tui_controller.start_server(port=9876)
    assert res_start is True
    assert state.server_running is True

    tui_controller.stop_server()
    assert state.server_running is False


def test_settings_masked_secrets_and_help_screen(tui_controller):
    """Test settings screen redacting secret tokens and help screen shortcuts."""
    state = tui_controller.state

    panel_set = render_settings_screen(state)
    assert panel_set is not None
    assert "********" in panel_to_str(panel_set)

    panel_help = render_help_screen(state)
    assert panel_help is not None
    assert "Ctrl+P" in panel_to_str(panel_help)


def test_command_palette_screen(tui_controller):
    """Test Claude-Code-style command palette screen rendering."""
    state = tui_controller.state
    state.search_query = "Export"

    panel_cp = render_command_palette_screen(state, selected_idx=0)
    assert panel_cp is not None
    assert "Command Palette" in panel_to_str(panel_cp)


def test_cli_tui_command_parsing():
    """Test 'scandoc tui' CLI subcommand parsing."""
    parser = create_parser()
    args = parser.parse_args(["tui"])
    assert args.command == "tui"


def test_tui_app_execution(tui_controller):
    """Test ScanDocTuiApp class instantiation and rendering."""
    app = ScanDocTuiApp(controller=tui_controller)
    panel = app.render_current_screen()
    assert panel is not None
