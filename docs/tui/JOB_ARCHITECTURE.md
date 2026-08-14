# Go TUI Background Job Architecture Specification

## Async Job Manager (`jobs.JobManager`)

Document processing, model downloading, and benchmarking tasks run as background goroutines without blocking the TUI event loop:

```go
package jobs

import (
    "context"
    "time"
)

type JobStatus string

const (
    JobQueued    JobStatus = "QUEUED"
    JobRunning   JobStatus = "RUNNING"
    JobCompleted JobStatus = "COMPLETED"
    JobFailed    JobStatus = "FAILED"
    JobCancelled JobStatus = "CANCELLED"
)

type Job struct {
    ID           string
    DocumentPath string
    TaskName     string
    Status       JobStatus
    ProgressPct  float64
    CurrentStage string
    StartedAt    time.Time
    FinishedAt   time.Time
    ErrorMessage string
    ResultData   any
    CancelFunc   context.CancelFunc
}

type JobManager struct {
    jobs map[string]*Job
}
```

## Goroutines & Cancellation Tokens

1. When a task starts, `JobManager.CreateJob` generates a unique `ID` and a `context.WithCancel(ctx)`.
2. A background worker goroutine processes pages asynchronously while emitting progress updates to `ProgressChannel`.
3. If the user presses `Esc` or cancels a job, `CancelFunc()` is invoked, signalling the worker goroutine to abort cleanly.
