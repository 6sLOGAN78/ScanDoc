package pipeline

import (
	"strings"
	"testing"

	"scandoc/internal/tui/state"
)

func TestPipelineRender(t *testing.T) {
	st := state.NewAppState()
	view := Render(st, 0)

	if !strings.Contains(view, "Pipeline Stage Configuration") {
		t.Errorf("Expected title in view, got: %s", view)
	}

	if !strings.Contains(view, "ADAPTIVE") {
		t.Errorf("Expected ADAPTIVE routing mode in view, got: %s", view)
	}
}
