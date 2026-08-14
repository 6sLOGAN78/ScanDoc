package document

import (
	"fmt"
	"strings"

	"scandoc/internal/tui/state"
	"scandoc/internal/tui/styles"
)

func Render(st *state.AppState, selectedIdx int) string {
	var b strings.Builder
	b.WriteString(styles.HeaderStyle.Render(" DocumentIR Inspector & Structural Tree ") + "\n\n")

	if st.ActiveDocumentPath == "" {
		b.WriteString(styles.NormalItemStyle.Render("No active document loaded for inspection.") + "\n")
		b.WriteString(styles.NormalItemStyle.Render("Select a file or folder from the main menu [1] or [2] to process a document first.") + "\n")
	} else {
		b.WriteString(styles.ActiveItemStyle.Render(fmt.Sprintf("Active File : %s", st.ActiveDocumentName)) + "\n")
		b.WriteString(styles.NormalItemStyle.Render(fmt.Sprintf("Disk Path   : %s", st.ActiveDocumentPath)) + "\n")
		b.WriteString(styles.NormalItemStyle.Render(fmt.Sprintf("Page Count  : %d pages", st.TotalPages)) + "\n\n")

		b.WriteString(styles.HeaderStyle.Render(" Extracted Structural Nodes ") + "\n")

		sampleBlocks := []struct {
			ID   string
			Type string
			Text string
			BBox string
		}{
			{"blk_h1_0", "HEADING (H1)", "Executive Overview & Summary", "[0.08, 0.06, 0.92, 0.10]"},
			{"blk_p_1", "PARAGRAPH", "This document contains processed invoice and table metrics.", "[0.08, 0.12, 0.92, 0.25]"},
			{"blk_tbl_2", "TABLE (2x2)", "Table 1: Quarterly Revenue Breakdown", "[0.08, 0.28, 0.92, 0.55]"},
			{"blk_math_3", "FORMULA", "$$E = mc^2$$ (LaTeX)", "[0.08, 0.58, 0.92, 0.65]"},
		}

		for i, block := range sampleBlocks {
			line := fmt.Sprintf("[%s] %-15s | %-38s | BBox: %s", block.ID, block.Type, block.Text, block.BBox)
			if i == selectedIdx {
				b.WriteString(styles.ActiveItemStyle.Render("› "+line) + "\n")
			} else {
				b.WriteString(styles.NormalItemStyle.Render("  "+line) + "\n")
			}
		}
	}

	b.WriteString("\n" + styles.FooterStyle.Render("Press Esc or Enter to return to Home Dashboard."))
	return styles.PanelStyle.Render(b.String())
}
