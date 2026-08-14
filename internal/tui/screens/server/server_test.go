package server

import (
	"strings"
	"testing"

	"scandoc/internal/tui/state"
)

func TestServerRender(t *testing.T) {
	st := state.NewAppState()
	st.ServerRunning = true

	view := Render(st)
	if !strings.Contains(view, "REST API & Visual Studio Web Server Control") {
		t.Errorf("Expected title in view, got: %s", view)
	}

	if !strings.Contains(view, "SERVER ACTIVE") {
		t.Errorf("Expected SERVER ACTIVE in view, got: %s", view)
	}
}
