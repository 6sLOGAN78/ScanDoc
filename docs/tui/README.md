# scanDOC Go TUI Documentation

Welcome to the documentation suite for the **scanDOC Native Go Terminal User Interface (TUI)**.

This directory documents the complete architectural specification, research rationale, migration matrix, and design patterns for the native Go implementation of scanDOC's interactive terminal interface.

---

## Documentation Index

- [GO_TUI_RESEARCH.md](GO_TUI_RESEARCH.md) — Framework evaluation (Bubble Tea vs. tview vs. termui) and architectural choice rationale.
- [ARCHITECTURE.md](ARCHITECTURE.md) — High-level architecture, Elm pattern, component hierarchy, and layer boundaries.
- [MIGRATION_PLAN.md](MIGRATION_PLAN.md) — 10-phase migration roadmap from Python TUI to Native Go TUI.
- [MIGRATION_MATRIX.md](MIGRATION_MATRIX.md) — Comprehensive Python-to-Go component, file, screen, and workflow mapping.
- [SCREEN_ARCHITECTURE.md](SCREEN_ARCHITECTURE.md) — Screen navigation, lifecycle states, layout models, and screen implementations.
- [STATE_ARCHITECTURE.md](STATE_ARCHITECTURE.md) — Centralized state tree (`AppState`), screen states, and immutable update flow.
- [EVENT_ARCHITECTURE.md](EVENT_ARCHITECTURE.md) — Typed event system, message passing (`tea.Msg`), and pub/sub bus.
- [COMMAND_ARCHITECTURE.md](COMMAND_ARCHITECTURE.md) — Command specification registry, keybindings, and Command Palette search engine.
- [JOB_ARCHITECTURE.md](JOB_ARCHITECTURE.md) — Asynchronous background job manager, worker goroutines, channels, and progress tracking.
- [BACKEND_BOUNDARY.md](BACKEND_BOUNDARY.md) — Service interfaces (`DocumentService`, `ModelService`, `BenchmarkService`, `ServerService`) decoupling TUI from core execution.
- [TESTING_STRATEGY.md](TESTING_STRATEGY.md) — Unit testing, message simulation, screen rendering tests, and integration smoke testing.

---

## Quick Reference

- **Language**: Go 1.25+
- **Core TUI Framework**: `github.com/charmbracelet/bubbletea`
- **Styling Engine**: `github.com/charmbracelet/lipgloss`
- **Component Library**: `github.com/charmbracelet/bubbles`
- **Executable Target**: `cmd/scandoc/main.go`
- **Package Location**: `internal/tui/`
