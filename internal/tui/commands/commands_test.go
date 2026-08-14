package commands

import (
	"testing"
)

func TestCommandRegistry(t *testing.T) {
	cr := NewCommandRegistry()
	cmds := cr.ListCommands("")

	if len(cmds) < 10 {
		t.Errorf("Expected at least 10 default commands, got %d", len(cmds))
	}

	filtered := cr.ListCommands("file")
	if len(filtered) == 0 {
		t.Errorf("Expected filtered commands for 'file', got 0")
	}

	cmd := cr.LookupKeybinding("Ctrl+O")
	if cmd == nil {
		t.Fatalf("Expected to find command for 'Ctrl+O', got nil")
	}

	if cmd.ID != "file.open" {
		t.Errorf("Expected command ID 'file.open', got '%s'", cmd.ID)
	}
}
