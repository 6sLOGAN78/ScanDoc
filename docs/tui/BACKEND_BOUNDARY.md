# Backend Boundary & Service Interfaces Specification

## Overview

The scanDOC Go TUI does NOT shell out to Python CLI commands for every screen or keypress. Instead, it relies on strongly-typed Go service interfaces (`backend.DocumentService`, `backend.ModelService`, `backend.BenchmarkService`, `backend.ServerService`).

## Go Service Interfaces

```go
package backend

import (
    "context"
)

type DocumentService interface {
    Inspect(ctx context.Context, path string) (*DocumentMetadata, error)
    Process(ctx context.Context, path string, config PipelineConfig) (*DocumentResult, error)
    Export(ctx context.Context, doc *DocumentIR, format string, outputDir string) (string, error)
}

type ModelService interface {
    ListModels(ctx context.Context) ([]ModelStatus, error)
    DownloadModel(ctx context.Context, modelID string) error
    ClearCache(ctx context.Context, modelID string) error
}

type BenchmarkService interface {
    RunBenchmark(ctx context.Context, rounds int) (*BenchmarkResult, error)
}

type ServerService interface {
    StartServer(ctx context.Context, host string, port int) error
    StopServer(ctx context.Context) error
    IsRunning() bool
}
```

## Backend Implementations

- **`NativeBackend`**: Uses direct IPC / C-Shared bindings or structured sub-process RPC to communicate with the core scanDOC engine.
- **`MockBackend`**: In-memory mock implementation used for unit testing, offline development, and instant TUI preview testing.
