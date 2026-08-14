package help

import (
	"strings"

	"github.com/charmbracelet/lipgloss"

	"scandoc/internal/tui/state"
	"scandoc/internal/tui/styles"
)

func Render(st *state.AppState) string {
	var b strings.Builder
	b.WriteString(styles.HeaderStyle.Render(" scanDOC Help & Keyboard Guide ") + "\n\n")

	b.WriteString(lipgloss.NewStyle().Bold(true).Foreground(styles.AccentColor).Render("Keyboard Navigation Cheat Sheet:") + "\n\n")

	shortcuts := [][2]string{
		{"1 .. 9", "Quick navigate to menu options"},
		{"w / s or ↑ / ↓", "Navigate up and down through list options"},
		{"Enter", "Select focused menu item or confirm action"},
		{"Space", "Toggle setting / multi-select file"},
		{"Ctrl+O / o", "Open Document File Browser"},
		{"Ctrl+F / f", "Open Folder Workspace Browser"},
		{"p", "Open Pipeline Configuration"},
		{"m", "Open Model Lifecycle Manager"},
		{"b", "Run CPU Benchmark Suite vs Docling"},
		{"s", "Manage REST API & Web Studio Server"},
		{"e", "Export active document to target format"},
		{"3", "Inspect active DocumentIR structure tree"},
		{"Ctrl+P or >", "Open Command Palette quick search modal"},
		{"Esc", "Return to Home Dashboard from any screen"},
		{"q or 0", "Quit scanDOC TUI"},
	}

	for _, sc := range shortcuts {
		b.WriteString(styles.ActiveItemStyle.Render(sc[0]) + strings.Repeat(" ", 20-len(sc[0])) + styles.NormalItemStyle.Render(sc[1]) + "\n")
	}

	b.WriteString("\n" + styles.FooterStyle.Render("Press Enter or Esc to return to Home Dashboard."))
	return styles.PanelStyle.Render(b.String())
}
