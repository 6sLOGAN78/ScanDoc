package export

import (
	"strings"
	"testing"

	"scandoc/internal/tui/state"
)

func TestExportRender(t *testing.T) {
	st := state.NewAppState()
	st.ActiveDocumentPath = "/tmp/invoice.pdf"
	st.ActiveDocumentName = "invoice.pdf"

	view := Render(st, 0)
	if !strings.Contains(view, "Multi-Format Exporter Studio") {
		t.Errorf("Expected title in view, got: %s", view)
	}

	if !strings.Contains(view, "markdown") {
		t.Errorf("Expected format markdown in view, got: %s", view)
	}
}
