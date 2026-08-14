# Go TUI State Architecture Specification

## Centralized State Tree (`AppState`)

State management in the scanDOC Go TUI is unified into a central `AppState` struct:

```go
package state

import (
    "time"
)

type AppState struct {
    // Navigation
    CurrentScreen  string
    PreviousScreen string

    // Workspace & File Selection
    CurrentDir      string
    SelectedPaths   []string
    SearchQuery     string
    ExtensionFilter string

    // Active Processing Document
    ActiveDocumentPath string
    ActiveDocumentName string
    ProcessingStatus   string // "idle", "processing", "completed", "failed", "cancelled"
    ProgressStage      string
    ProgressPct        float64
    CurrentPage        int
    TotalPages         int
    ProcessingErrors   []string
    ProcessingLogs     []string

    // Pipeline & Hardware Configuration
    RoutingMode    string // "adaptive", "fast", "deep", "fallback"
    EnableOCR      bool
    EnableLayout   bool
    EnableTable    bool
    EnableFormula  bool
    EnableVLM      bool
    OfflineMode    bool
    DeviceType     string // "cpu", "cuda", "openvino"
    PrecisionMode  string // "fp32", "fp16", "int8"

    // Export Configuration
    ExportFormat    string
    ExportOutputDir string

    // Server State
    ServerRunning bool
    ServerHost    string
    ServerPort    int

    // History
    RecentDocuments []RecentDocument
}

type RecentDocument struct {
    Name      string    `json:"name"`
    Path      string    `json:"path"`
    Status    string    `json:"status"`
    SizeBytes int64     `json:"size_bytes"`
    Timestamp time.Time `json:"timestamp"`
}
```

## State Mutators & Immutability

In Bubble Tea, models receive messages and return modified models. The `AppState` tree is updated deterministically in response to typed messages (`tea.Msg`), ensuring thread-safe UI updates without direct variable mutation locks.
