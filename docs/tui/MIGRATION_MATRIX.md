# Python → Go TUI Component Migration Matrix

| Python Component | Responsibility | Go Component | Migration Status |
|---|---|---|---|
| `src/scandoc/tui/app.py` | Main interactive application loop & Rich renderer | `internal/tui/app/app.go` | Planned |
| `src/scandoc/tui/controller.py` | Application controller orchestrating backend calls | `internal/tui/controller/controller.go` | Planned |
| `src/scandoc/tui/state.py` | Reactive state tree & screen types | `internal/tui/state/state.go` | Planned |
| `src/scandoc/tui/events.py` | Decoupled event bus & event types | `internal/tui/events/events.go` | Planned |
| `src/scandoc/tui/job_manager.py` | Background job manager & task tracking | `internal/tui/jobs/jobs.go` | Planned |
| `src/scandoc/tui/command_registry.py` | Keybindings & Command Palette registry | `internal/tui/commands/commands.go` | Planned |
| `src/scandoc/tui/screens/home.py` | Home Dashboard screen renderer | `internal/tui/screens/home/home.go` | Planned |
| `src/scandoc/tui/screens/file_picker.py` | Interactive File/Folder Picker screen renderer | `internal/tui/screens/filepicker/filepicker.go` | Planned |
| `src/scandoc/tui/screens/pipeline.py` | Pipeline Configuration screen renderer | `internal/tui/screens/pipeline/pipeline.go` | Planned |
| `src/scandoc/tui/screens/processing.py` | Processing Progress Monitor screen renderer | `internal/tui/screens/processing/processing.go` | Planned |
| `src/scandoc/tui/screens/document.py` | DocumentIR Inspector screen renderer | `internal/tui/screens/document/document.go` | Planned |
| `src/scandoc/tui/screens/models.py` | Model Lifecycle Manager screen renderer | `internal/tui/screens/models/models.go` | Planned |
| `src/scandoc/tui/screens/benchmark.py` | Benchmark Suite screen renderer | `internal/tui/screens/benchmark/benchmark.go` | Planned |
| `src/scandoc/tui/screens/export.py` | Multi-Format Exporter Studio screen renderer | `internal/tui/screens/export/export.go` | Planned |
| `src/scandoc/tui/screens/server.py` | REST API Server Control screen renderer | `internal/tui/screens/server/server.go` | Planned |
| `src/scandoc/tui/screens/settings.py` | Settings & Device Config screen renderer | `internal/tui/screens/settings/settings.go` | Planned |
| `src/scandoc/tui/screens/help.py` | Help & Keyboard Reference screen renderer | `internal/tui/screens/help/help.go` | Planned |
| `src/scandoc/tui/screens/command_palette.py` | Command Palette Search Modal renderer | `internal/tui/screens/commandpalette/commandpalette.go` | Planned |
| `src/scandoc/cli/commands/tui.py` | CLI TUI entry point launcher | `src/scandoc/cli/commands/tui.py` / `cmd/scandoc` | Planned |
