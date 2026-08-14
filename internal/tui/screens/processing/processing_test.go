package processing

import (
	"strings"
	"testing"

	"scandoc/internal/tui/state"
)

func TestProcessingRender(t *testing.T) {
	st := state.NewAppState()
	st.ProcessingStatus = "processing"
	st.ProgressPct = 45.0
	st.ProgressStage = "OCR Stage"

	view := Render(st)
	if !strings.Contains(view, "Pipeline Processing Monitor") {
		t.Errorf("Expected title in view, got: %s", view)
	}

	if !strings.Contains(view, "45.0%") {
		t.Errorf("Expected 45.0%% progress in view, got: %s", view)
	}
}
