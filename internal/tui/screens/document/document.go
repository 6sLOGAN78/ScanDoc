package document

import (
	"fmt"
	"strings"

	"scandoc/internal/tui/state"
	"scandoc/internal/tui/styles"
)

func Render(st *state.AppState, selectedIdx int) string {
	var b strings.Builder
	
	if st.ActiveDocumentPath == "" {
		b.WriteString(styles.TitleStyle.Render("Inspector") + "\n\n")
		b.WriteString(styles.MutedStyle.Render("  No document selected.") + "\n")
		b.WriteString("\n" + styles.FooterStyle.Render("Esc Back"))
		return b.String()
	}

	docName := st.ActiveDocumentName
	if docName == "" {
		docName = "document"
	}

	// Breadcrumb header
	b.WriteString(styles.TitleStyle.Render(fmt.Sprintf("%s / Page %d", docName, st.CurrentPage)) + "\n\n")

	// Tabs mock
	b.WriteString(styles.PrimaryStyle.Render("  Content") + "   " + 
				  styles.MutedStyle.Render("Layout   JSON   Relations") + "\n\n")

	sampleBlocks := []struct {
		ID   string
		Type string
		Text string
		BBox string
	}{
		{"blk_01", "Heading", "Executive Overview & Summary", "0.08, 0.06"},
		{"blk_02", "Paragraph", "This document contains processed invoice metrics.", "0.08, 0.12"},
		{"blk_03", "Table", "Table 1: Quarterly Revenue Breakdown", "0.08, 0.28"},
		{"blk_04", "Formula", "$$E = mc^2$$", "0.08, 0.58"},
	}

	for i, block := range sampleBlocks {
		if i == selectedIdx {
			b.WriteString(styles.SelectedItemStyle.Render(fmt.Sprintf("> %s", block.Type)) + "\n")
			b.WriteString(styles.PrimaryStyle.Render(fmt.Sprintf("  %s", block.Text)) + "\n")
			b.WriteString(styles.MutedStyle.Render(fmt.Sprintf("  ID: %s   Pos: [%s]", block.ID, block.BBox)) + "\n\n")
		} else {
			b.WriteString(styles.SecondaryStyle.Render(fmt.Sprintf("  %s", block.Type)) + "\n")
			b.WriteString(styles.MutedStyle.Render(fmt.Sprintf("  %s", block.Text)) + "\n\n")
		}
	}

	sepWidth := st.WindowWidth - 25
	if sepWidth < 10 {
		sepWidth = 50
	}
	
	b.WriteString(styles.MutedStyle.Render(strings.Repeat("─", sepWidth)) + "\n")
	b.WriteString(styles.FooterStyle.Render("↑/↓ Navigate   Tab Switch view   Esc Back"))
	return b.String()
}
