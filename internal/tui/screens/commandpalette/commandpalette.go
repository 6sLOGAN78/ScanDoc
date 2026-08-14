package commandpalette

import (
	"fmt"
	"strings"

	"scandoc/internal/tui/commands"
	"scandoc/internal/tui/state"
	"scandoc/internal/tui/styles"
)

func Render(st *state.AppState, selectedIdx int) string {
	var b strings.Builder
	b.WriteString(styles.HeaderStyle.Render(" Command Palette ") + "\n\n")

	b.WriteString(styles.ActiveItemStyle.Render(fmt.Sprintf("Search: %s_", st.SearchQuery)) + "\n\n")

	cmds := commands.DefaultCommandRegistry.ListCommands(st.SearchQuery)
	if len(cmds) == 0 {
		b.WriteString(styles.NormalItemStyle.Render("No matching commands found.") + "\n")
	} else {
		for i, cmd := range cmds {
			if i == selectedIdx {
				b.WriteString(styles.ActiveItemStyle.Render(fmt.Sprintf("› [%-8s] %-30s | %s", cmd.Category, cmd.Title, cmd.Keybinding)) + "\n")
			} else {
				b.WriteString(styles.NormalItemStyle.Render(fmt.Sprintf("  [%-8s] %-30s | %s", cmd.Category, cmd.Title, cmd.Keybinding)) + "\n")
			}
		}
	}

	b.WriteString("\n" + styles.FooterStyle.Render("Type to filter | ↑/↓ to select | Enter to execute | Esc to close"))
	return styles.PanelStyle.Render(b.String())
}
