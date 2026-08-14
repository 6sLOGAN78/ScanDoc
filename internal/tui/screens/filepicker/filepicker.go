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
	
	// Header
	b.WriteString(styles.TitleStyle.Render(st.CurrentDir) + "\n\n")

	if len(items) == 0 {
		b.WriteString(styles.MutedStyle.Render("  Directory is empty.") + "\n")
	} else {
		// Calculate visible window
		visibleCount := st.WindowHeight - 12
		if visibleCount < 5 {
			visibleCount = 10
		}
		
		startIdx := 0
		if selectedIdx >= visibleCount/2 {
			startIdx = selectedIdx - visibleCount/2
		}
		endIdx := startIdx + visibleCount
		if endIdx > len(items) {
			endIdx = len(items)
			startIdx = endIdx - visibleCount
			if startIdx < 0 {
				startIdx = 0
			}
		}

		if startIdx > 0 {
			b.WriteString(styles.MutedStyle.Render("  ↑ ..."))
			b.WriteString("\n")
		}

		for i := startIdx; i < endIdx; i++ {
			item := items[i]
			
			typeDesc := "FILE"
			if item.IsDir {
				typeDesc = "<DIR>"
			} else if item.FormatDesc != "" {
				typeDesc = strings.ToUpper(item.FormatDesc)
			}

			selectedTag := " "
			for _, p := range st.SelectedPaths {
				if p == item.Path {
					selectedTag = "*"
					break
				}
			}

			sizeStr := ""
			if !item.IsDir {
				sizeStr = fmt.Sprintf("%d KB", item.SizeBytes/1024)
				if item.SizeBytes > 1024*1024 {
					sizeStr = fmt.Sprintf("%d MB", item.SizeBytes/(1024*1024))
				}
			}

			// Format: [tag] <DIR> name  size
			// e.g.  *  <DIR> projects/
			//       PDF   thesis.pdf   12 MB
			
			nameStr := item.Name
			if item.IsDir {
				nameStr += "/"
			}

			line := fmt.Sprintf("%s  %-6s %-35s %s", selectedTag, typeDesc, nameStr, sizeStr)
			if i == selectedIdx {
				b.WriteString(styles.SelectedItemStyle.Render(">"+line[1:]) + "\n")
			} else {
				b.WriteString(styles.NormalItemStyle.Render(" "+line[1:]) + "\n")
			}
		}

		if endIdx < len(items) {
			b.WriteString(styles.MutedStyle.Render("  ↓ ..."))
			b.WriteString("\n")
		}
	}

	sepWidth := st.WindowWidth - 25
	if sepWidth < 10 {
		sepWidth = 50
	}
	b.WriteString("\n" + styles.MutedStyle.Render(strings.Repeat("─", sepWidth)) + "\n")
	b.WriteString(styles.FooterStyle.Render("Enter Open    Space Select    Backspace Up    / Search"))
	return b.String()
}
