package home

import (
	"strings"
	"testing"

	"scandoc/internal/tui/state"
)

func TestHomeRender(t *testing.T) {
	st := state.NewAppState()
	view := Render(st, 0)

	if !strings.Contains(view, "Dashboard") {
		t.Errorf("Expected view to contain 'Dashboard', got: %s", view)
	}

	if !strings.Contains(view, "Recent") {
		t.Errorf("Expected view to contain 'Recent', got: %s", view)
	}
}
