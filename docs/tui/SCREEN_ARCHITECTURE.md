# Go TUI Screen Architecture & Navigation Specification

## Overview

The scanDOC Go TUI implements a modular screen architecture. Each screen implements a sub-model interface within Bubble Tea.

## Screen Inventory

1. **Home Screen (`internal/tui/screens/home`)**: Dashboard menu with 10 primary action items (`1. Open File`, `2. Open Folder`, `3. Document Inspector`, `4. Model Manager`, `5. Pipeline Config`, `6. Benchmark`, `7. Server`, `8. Settings`, `9. Help`, `Q. Quit`).
2. **File & Folder Picker (`internal/tui/screens/filepicker`)**: Interactive file system browser supporting directory navigation, file selection, search filter, and extension filtering.
3. **Pipeline Configuration (`internal/tui/screens/pipeline`)**: Interactive editor for toggling pipeline stages (OCR, Layout, Table, Formula, VLM), routing modes (`adaptive`, `fast`, `deep`, `fallback`), and offline mode.
4. **Processing Monitor (`internal/tui/screens/processing`)**: Real-time progress bar, stage indicator, log stream, and error list during document conversion tasks.
5. **DocumentIR Inspector (`internal/tui/screens/document`)**: Tree viewer for inspect page count, metadata, block types, bounding boxes, and extracted text.
6. **Model Manager (`internal/tui/screens/models`)**: Model lifecycle dashboard showing install status, file size, download trigger (`d`), and cache clearing (`c`).
7. **Benchmark Suite (`internal/tui/screens/benchmark`)**: Benchmark execution screen comparing scanDOC vs Docling throughput.
8. **Export Studio (`internal/tui/screens/export`)**: Selector for 8 output formats (Markdown, HTML, JSON, Text, DOCX, EPUB, PDF/A, RAG JSON).
9. **Server Manager (`internal/tui/screens/server`)**: REST API & Web Studio server control panel (Host/Port, Start/Stop status).
10. **Settings Screen (`internal/tui/screens/settings`)**: Offline mode toggle, device selection (CPU, CUDA, OpenVINO), and precision modes.
11. **Help Screen (`internal/tui/screens/help`)**: Complete keyboard shortcut reference guide.
12. **Command Palette (`internal/tui/screens/commandpalette`)**: Searchable action modal (`Ctrl+P` / `>`) with fuzzy query filter.

## Screen Navigation Stack

```go
type Navigation struct {
    CurrentScreen  ScreenID
    PreviousScreen ScreenID
    History        []ScreenID
}
```
- `NavigateTo(screen ScreenID)` pushes active screen onto history.
- `NavigateBack()` pops history stack or defaults to `ScreenHome`.
- Pressing `Esc` at any screen returns to `ScreenHome`.
