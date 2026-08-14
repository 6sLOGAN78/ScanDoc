package home

import (
	"strings"
	"testing"

	"scandoc/internal/tui/state"
)

func TestHomeRender(t *testing.T) {
	st := state.NewAppState()
	view := Render(st, 0)

	if !strings.Contains(view, "scanDOC Document Intelligence Engine") {
		t.Errorf("Expected view to contain banner, got: %s", view)
	}

	if !strings.Contains(view, "Open File") {
		t.Errorf("Expected view to contain 'Open File', got: %s", view)
	}
}
