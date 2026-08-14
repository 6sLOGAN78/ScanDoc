# Native Go TUI Migration Plan

## 10-Phase Migration Roadmap

### Phase 1: Repository + TUI Research & Architectural Specification (CURRENT)
- Thorough analysis of existing Python TUI implementation.
- Framework research and selection (Bubble Tea + Lip Gloss + Bubbles).
- Authoring complete architectural specification and migration matrix in `docs/tui/`.

### Phase 2: Go Foundation Infrastructure
- Initialize `go.mod` (Go 1.25).
- Create `internal/tui/state`, `internal/tui/events`, `internal/tui/jobs`, `internal/tui/commands`, `internal/tui/backend`, `internal/tui/styles`, `internal/tui/app`.
- Build base Bubble Tea main model, screen router, theme tokens, and mock backend adapters.

### Phase 3: Core UI Screens Implementation
- Implement `Home` dashboard screen.
- Implement `Help` shortcut reference screen.
- Implement `Settings` configuration screen.
- Implement `Command Palette` modal search engine.
- Implement `File Picker` & `Folder Picker` directory browser.

### Phase 4: Document Processing Workflow
- Implement `Document Inspector` structure tree viewer.
- Implement `Processing` progress monitor screen.
- Integrate async pipeline job execution via worker goroutines, progress channels, and cancellation tokens.

### Phase 5: Pipeline Configuration Workflow
- Implement `Pipeline Config` editor screen.
- Allow configuring OCR, layout, table, formula, VLM toggles, and routing modes (`adaptive`, `fast`, `deep`, `fallback`).

### Phase 6: Model Management Workflow
- Implement `Model Manager` lifecycle dashboard screen.
- Integrate model list, download progress, checksum verification, and cache clearing.

### Phase 7: Benchmarking Workflow
- Implement `Benchmark` configuration and execution screen.
- Display real-time CPU throughput comparison vs Docling.

### Phase 8: Export & Server Workflows
- Implement `Export Studio` multi-format exporter screen (8 target formats).
- Implement `Server Manager` control panel screen (start/stop REST API & Web Studio).

### Phase 9: CLI Integration & System Parity Verification
- Create entrypoint in `cmd/scandoc/main.go`.
- Connect Python CLI (`scandoc tui`) to launch native Go TUI binary seamlessly.
- Verify complete behavioral parity against Python reference.

### Phase 10: Codebase Cleanup & Final Release
- Safely deprecate legacy Python TUI modules.
- Update `README.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`.
- Verify `go test ./...` and `pytest`.
