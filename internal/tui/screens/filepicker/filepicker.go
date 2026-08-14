package filepicker

import (
	"fmt"
	"strings"

	"scandoc/internal/tui/controller"
	"scandoc/internal/tui/state"
	"scandoc/internal/tui/styles"
)

func Render(st *state.AppState, items []controller.FileItem, selectedIdx int) string {
	var b strings.Builder
	title := " File Browser "
	if st.CurrentScreen == state.ScreenFolderPicker {
		title = " Folder Workspace Browser "
	}
	b.WriteString(styles.HeaderStyle.Render(title) + "\n\n")

	b.WriteString(styles.NormalItemStyle.Render(fmt.Sprintf("Directory: %s", st.CurrentDir)) + "\n\n")

	if len(items) == 0 {
		b.WriteString(styles.NormalItemStyle.Render("Directory is empty.") + "\n")
	} else {
		for i, item := range items {
			icon := "📄"
			if item.IsDir {
				icon = "📁"
			}

			selectedTag := " "
			for _, p := range st.SelectedPaths {
				if p == item.Path {
					selectedTag = "✓"
					break
				}
			}

			sizeStr := ""
			if !item.IsDir {
				sizeStr = fmt.Sprintf("%d KB", item.SizeBytes/1024)
			}

			line := fmt.Sprintf("[%s] %s %-35s %-8s %s", selectedTag, icon, item.Name, item.FormatDesc, sizeStr)
			if i == selectedIdx {
				b.WriteString(styles.ActiveItemStyle.Render("› "+line) + "\n")
			} else {
				b.WriteString(styles.NormalItemStyle.Render("  "+line) + "\n")
			}
		}
	}

	b.WriteString("\n" + styles.FooterStyle.Render("Space: select | Enter: open/process | Backspace/b: parent directory | Esc: Home"))
	return styles.PanelStyle.Render(b.String())
}
