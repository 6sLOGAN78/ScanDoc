# Go TUI Event Architecture Specification

## Typed Messages & Message Flow

Bubble Tea uses typed messages (`tea.Msg`) for all events. scanDOC defines strong event types:

```go
package events

import "time"

type EventType string

const (
    EventDocumentImported   EventType = "document.imported"
    EventProcessingStarted  EventType = "processing.started"
    EventStageStarted       EventType = "stage.started"
    EventStageCompleted     EventType = "stage.completed"
    EventProcessingCompleted EventType = "processing.completed"
    EventProcessingFailed    EventType = "processing.failed"
    EventJobStatusChanged   EventType = "job.status_changed"
    EventModelStatusChanged EventType = "model.status_changed"
    EventLogEmitted         EventType = "log.emitted"
    EventServerStatusChanged EventType = "server.status_changed"
)

type AppEvent struct {
    Type      EventType
    Timestamp time.Time
    Payload   map[string]any
    Message   string
}

// Bubble Tea tea.Msg Wrapper
type AppEventMsg AppEvent
```

## Event Bus Integration

In addition to Bubble Tea's built-in message queue, `EventBus` provides a thread-safe pub/sub bus for background worker goroutines:

```go
type EventBus struct {
    subscribers map[EventType][]func(AppEvent)
}

func (b *EventBus) Subscribe(eventType EventType, callback func(AppEvent))
func (b *EventBus) Publish(event AppEvent)
```
- Background goroutines publish events to `EventBus`.
- The main Bubble Tea update loop converts `AppEvent` into `AppEventMsg` commands (`tea.Cmd`) to refresh the TUI canvas safely.
