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
	
	sepWidth := st.WindowWidth - 25
	if sepWidth < 10 {
		sepWidth = 50
	}
	
	// Input area
	b.WriteString(styles.TitleStyle.Render("Command Palette") + "\n\n")
	b.WriteString(styles.PrimaryStyle.Render(fmt.Sprintf("> %s_", st.SearchQuery)) + "\n")
	b.WriteString(styles.MutedStyle.Render(strings.Repeat("─", sepWidth)) + "\n\n")

	cmds := commands.DefaultCommandRegistry.ListCommands(st.SearchQuery)
	if len(cmds) == 0 {
		b.WriteString(styles.MutedStyle.Render("  No matching commands") + "\n")
	} else {
		for i, cmd := range cmds {
			if i == selectedIdx {
				b.WriteString(styles.SelectedItemStyle.Render(fmt.Sprintf("  %-30s  %s", cmd.Title, cmd.Keybinding)) + "\n")
			} else {
				b.WriteString(styles.NormalItemStyle.Render(fmt.Sprintf("  %-30s  %s", cmd.Title, cmd.Keybinding)) + "\n")
			}
		}
	}

	b.WriteString("\n" + styles.MutedStyle.Render(strings.Repeat("─", sepWidth)) + "\n")
	b.WriteString(styles.FooterStyle.Render("Enter Execute   ↑/↓ Select   Esc Cancel"))
	return b.String()
}
