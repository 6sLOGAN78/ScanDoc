# Go TUI Testing Strategy Specification

## Overview

The native Go TUI test suite guarantees state predictability, screen navigation accuracy, message handling correctness, and backend service integration.

## Testing Layers

1. **Unit Tests (`internal/tui/*_test.go`)**:
   - `state_test.go`: Tests state tree initialization, navigation actions, log trimming, and offline mode toggles.
   - `events_test.go`: Tests event bus subscription, callback dispatching, and thread safety.
   - `jobs_test.go`: Tests job creation, status updates, list sorting, and cancellation token execution.
   - `commands_test.go`: Tests command registration, keybinding lookup, and fuzzy filter search queries.

2. **Screen Rendering & View Tests (`internal/tui/screens/*_test.go`)**:
   - Tests `Init()`, `Update(msg)`, and `View()` across all 12 screens.
   - Verifies that keypress messages (`tea.KeyMsg`) trigger appropriate screen state transitions.

3. **Backend Service Mock Tests (`internal/tui/backend/*_test.go`)**:
   - Verifies `MockBackend` implementations for document inspection, processing, model downloading, benchmarking, and server control.

4. **Integration & Smoke Tests (`cmd/scandoc/*_test.go`)**:
   - End-to-end headless Bubble Tea program verification simulating user workflows (`tea.NewProgram(model, tea.WithInput(input))`).

## Test Execution Command

```bash
go test ./... -v -cover
```
