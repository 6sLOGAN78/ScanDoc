package commands

import (
	"strings"

	"scandoc/internal/tui/state"
)

type CommandSpec struct {
	ID           string `json:"id"`
	Title        string `json:"title"`
	Category     string `json:"category"`
	Keybinding   string `json:"keybinding"`
	Description  string `json:"description"`
	TargetScreen string `json:"target_screen"`
}

type CommandRegistry struct {
	commands map[string]CommandSpec
}

func NewCommandRegistry() *CommandRegistry {
	r := &CommandRegistry{
		commands: make(map[string]CommandSpec),
	}
	r.registerDefaults()
	return r
}

func (r *CommandRegistry) registerDefaults() {
	defaults := []CommandSpec{
		{ID: "file.open", Title: "Open Document File", Category: "File", Keybinding: "Ctrl+O / o", Description: "Open interactive file browser", TargetScreen: state.ScreenFilePicker},
		{ID: "folder.open", Title: "Open Folder Workspace", Category: "File", Keybinding: "Ctrl+F / f", Description: "Open interactive folder browser", TargetScreen: state.ScreenFolderPicker},
		{ID: "pipeline.config", Title: "Configure Pipeline Engine", Category: "Pipeline", Keybinding: "p", Description: "Open pipeline stage editor", TargetScreen: state.ScreenPipelineConfig},
		{ID: "models.manager", Title: "Manage Local ML Models", Category: "Models", Keybinding: "m", Description: "Open model lifecycle dashboard", TargetScreen: state.ScreenModelManager},
		{ID: "benchmark.run", Title: "Run Performance Benchmark", Category: "Tools", Keybinding: "b", Description: "Run benchmark suite vs Docling", TargetScreen: state.ScreenBenchmark},
		{ID: "server.manage", Title: "REST Server Manager", Category: "Tools", Keybinding: "s", Description: "Start/stop REST API & Web Studio", TargetScreen: state.ScreenServerManager},
		{ID: "export.studio", Title: "Multi-Format Exporter Studio", Category: "Export", Keybinding: "e", Description: "Export DocumentIR to target format", TargetScreen: state.ScreenExport},
		{ID: "document.inspector", Title: "Inspect DocumentIR Structure", Category: "View", Keybinding: "3", Description: "Inspect block tree and page IR", TargetScreen: state.ScreenDocumentInspector},
		{ID: "command.palette", Title: "Open Command Palette", Category: "View", Keybinding: "Ctrl+P / >", Description: "Quick action search modal", TargetScreen: state.ScreenCommandPalette},
		{ID: "settings.open", Title: "System Settings", Category: "System", Keybinding: "8", Description: "Configure offline mode and devices", TargetScreen: state.ScreenSettings},
		{ID: "help.open", Title: "Help & Keyboard Guide", Category: "System", Keybinding: "? / h", Description: "Keyboard shortcut reference", TargetScreen: state.ScreenHelp},
	}

	for _, cmd := range defaults {
		r.Register(cmd)
	}
}

func (r *CommandRegistry) Register(cmd CommandSpec) {
	r.commands[cmd.ID] = cmd
}

func (r *CommandRegistry) ListCommands(filterQuery string) []CommandSpec {
	res := make([]CommandSpec, 0, len(r.commands))
	q := strings.ToLower(strings.TrimSpace(filterQuery))

	for _, cmd := range r.commands {
		if q == "" || strings.Contains(strings.ToLower(cmd.Title), q) ||
			strings.Contains(strings.ToLower(cmd.Category), q) ||
			strings.Contains(strings.ToLower(cmd.Description), q) {
			res = append(res, cmd)
		}
	}

	return res
}

func (r *CommandRegistry) LookupKeybinding(keybinding string) *CommandSpec {
	kb := strings.ToLower(strings.TrimSpace(keybinding))
	for _, cmd := range r.commands {
		if strings.Contains(strings.ToLower(cmd.Keybinding), kb) {
			return &cmd
		}
	}
	return nil
}

var DefaultCommandRegistry = NewCommandRegistry()
