package benchmark

import (
	"strings"
	"testing"

	"scandoc/internal/tui/state"
)

func TestBenchmarkRender(t *testing.T) {
	st := state.NewAppState()
	res := map[string]any{
		"scandoc_fps": 45.2,
		"docling_fps": 12.4,
		"speedup":     3.64,
	}

	view := Render(st, res, false)
	if !strings.Contains(view, "Performance Benchmark Suite") {
		t.Errorf("Expected title in view, got: %s", view)
	}

	if !strings.Contains(view, "45.2 pages/sec") {
		t.Errorf("Expected 45.2 pages/sec in view, got: %s", view)
	}
}
