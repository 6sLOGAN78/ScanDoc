# Native Go TUI System Architecture

## Architecture Overview

The native Go TUI for scanDOC is structured around a clean **5-Layer Architecture** implementing the Elm pattern (Model-View-Update).

```
┌─────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                  │
│   internal/tui/screens/ (Home, Document, Processing,   │
│   Pipeline, Models, Benchmark, Export, Server, etc.)    │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│                     APPLICATION & TUI MODEL             │
│   internal/tui/app (Main Model, Init, Update, View)     │
│   internal/tui/navigation (Screen Stack & Router)      │
│   internal/tui/commands (Command Registry & Palette)   │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│                   STATE & EVENT MANAGEMENT              │
│   internal/tui/state (AppState Tree)                    │
│   internal/tui/events (Event Bus & Typed Messages)      │
│   internal/tui/jobs (Async Job Manager & Goroutines)    │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│                     BACKEND BOUNDARY                    │
│   internal/tui/backend (DocumentService, ModelService,  │
│   BenchmarkService, ServerService Interfaces)           │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│                    SCAN-DOC CORE ENGINE                 │
│   Python Executable / C-Shared / RPC Core Bridge        │
└─────────────────────────────────────────────────────────┘
```

---

## Component Layout

```text
cmd/
└── scandoc/
    └── main.go                  # Main entrypoint

internal/
└── tui/
    ├── app/                     # Main Bubble Tea app model & event loop
    ├── backend/                 # Backend service interfaces & implementations
    ├── commands/                # Command Registry & Command Palette engine
    ├── components/              # Reusable UI widgets (Header, Footer, LogView, Progress)
    ├── controller/              # Application controller orchestrating actions
    ├── events/                  # Typed Event bus & Bubble Tea Msg definitions
    ├── jobs/                    # Async Job Manager, status tracking, worker goroutines
    ├── navigation/              # Screen state stack router
    ├── screens/                 # 12 Individual Screen models (Home, FilePicker, etc.)
    │   ├── benchmark/
    │   ├── commandpalette/
    │   ├── document/
    │   ├── export/
    │   ├── filepicker/
    │   ├── help/
    │   ├── home/
    │   ├── models/
    │   ├── pipeline/
    │   ├── processing/
    │   ├── server/
    │   └── settings/
    ├── state/                   # AppState root state tree
    ├── styles/                  # Theme colors, typography, borders, and Lip Gloss rules
    └── testutil/                # Test fixtures, mock backend services, and tea.Msg harness
```
