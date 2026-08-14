package events

import (
	"sync"
	"testing"
	"time"
)

func TestEventBusPubSub(t *testing.T) {
	bus := NewEventBus()

	var wg sync.WaitGroup
	wg.Add(1)

	var received string
	bus.Subscribe(EventProcessingStarted, func(ev AppEvent) {
		received = ev.Message
		wg.Done()
	})

	bus.Publish(AppEvent{
		Type:      EventProcessingStarted,
		Timestamp: time.Now(),
		Message:   "Test started",
	})

	wg.Wait()
	if received != "Test started" {
		t.Errorf("Expected message 'Test started', got '%s'", received)
	}
}
