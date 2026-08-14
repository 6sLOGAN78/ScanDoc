package events

import (
	"sync"
	"time"

	tea "github.com/charmbracelet/bubbletea"
)

type EventType string

const (
	EventDocumentImported    EventType = "document.imported"
	EventProcessingStarted   EventType = "processing.started"
	EventStageStarted        EventType = "stage.started"
	EventStageCompleted      EventType = "stage.completed"
	EventProcessingCompleted EventType = "processing.completed"
	EventProcessingFailed    EventType = "processing.failed"
	EventJobStatusChanged    EventType = "job.status_changed"
	EventModelStatusChanged  EventType = "model.status_changed"
	EventLogEmitted          EventType = "log.emitted"
	EventServerStatusChanged EventType = "server.status_changed"
)

type AppEvent struct {
	Type      EventType      `json:"type"`
	Timestamp time.Time      `json:"timestamp"`
	Payload   map[string]any `json:"payload"`
	Message   string         `json:"message"`
}

// Bubble Tea Message Wrapper
type AppEventMsg AppEvent

type EventBus struct {
	mu          sync.RWMutex
	subscribers map[EventType][]func(AppEvent)
}

func NewEventBus() *EventBus {
	return &EventBus{
		subscribers: make(map[EventType][]func(AppEvent)),
	}
}

func (b *EventBus) Subscribe(eventType EventType, callback func(AppEvent)) {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.subscribers[eventType] = append(b.subscribers[eventType], callback)
}

func (b *EventBus) Publish(event AppEvent) {
	b.mu.RLock()
	subs := b.subscribers[event.Type]
	callbacks := make([]func(AppEvent), len(subs))
	copy(callbacks, subs)
	b.mu.RUnlock()

	for _, cb := range callbacks {
		func() {
			defer func() { recover() }()
			cb(event)
		}()
	}
}

// EmitCmd returns a tea.Cmd for sending an event into Bubble Tea model Update
func EmitCmd(event AppEvent) tea.Cmd {
	return func() tea.Msg {
		if event.Timestamp.IsZero() {
			event.Timestamp = time.Now()
		}
		return AppEventMsg(event)
	}
}

var DefaultEventBus = NewEventBus()
