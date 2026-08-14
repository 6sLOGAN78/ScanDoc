package state

import (
	"testing"
)

func TestAppStateInitialization(t *testing.T) {
	st := NewAppState()
	if st.CurrentScreen != ScreenHome {
		t.Errorf("Expected initial screen %s, got %s", ScreenHome, st.CurrentScreen)
	}
	if st.ExportFormat != "markdown" {
		t.Errorf("Expected initial format 'markdown', got '%s'", st.ExportFormat)
	}
}

func TestNavigation(t *testing.T) {
	st := NewAppState()
	st.NavigateTo(ScreenFilePicker)
	if st.CurrentScreen != ScreenFilePicker {
		t.Errorf("Expected current screen %s, got %s", ScreenFilePicker, st.CurrentScreen)
	}
	if st.PreviousScreen != ScreenHome {
		t.Errorf("Expected previous screen %s, got %s", ScreenHome, st.PreviousScreen)
	}

	st.NavigateBack()
	if st.CurrentScreen != ScreenHome {
		t.Errorf("Expected current screen %s, got %s", ScreenHome, st.CurrentScreen)
	}
}

func TestOfflineModeToggle(t *testing.T) {
	st := NewAppState()
	initial := st.IsOffline()
	toggled := st.ToggleOfflineMode()

	if toggled == initial {
		t.Errorf("Expected offline mode to toggle from %v, got %v", initial, toggled)
	}
}

func TestLogsAndRecent(t *testing.T) {
	st := NewAppState()
	st.AddLog("Test message")
	if len(st.ProcessingLogs) != 1 {
		t.Errorf("Expected 1 log entry, got %d", len(st.ProcessingLogs))
	}

	st.AddRecent("/tmp/test.pdf", "completed")
	if len(st.RecentDocuments) != 1 {
		t.Errorf("Expected 1 recent document entry, got %d", len(st.RecentDocuments))
	}
}
