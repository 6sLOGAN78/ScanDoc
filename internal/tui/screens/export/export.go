package export

import (
	"fmt"
	"strings"

	"scandoc/internal/tui/state"
	"scandoc/internal/tui/styles"
)

type FormatOption struct {
	ID   string
	Name string
	Ext  string
}

func GetSupportedFormats() []FormatOption {
	return []FormatOption{
		{ID: "markdown", Name: "GitHub-Flavored Markdown", Ext: ".md"},
		{ID: "html", Name: "Semantic HTML5 Web Page", Ext: ".html"},
		{ID: "json", Name: "Lossless DocumentIR JSON", Ext: ".json"},
		{ID: "text", Name: "Plain Text Extraction", Ext: ".txt"},
		{ID: "docx", Name: "Microsoft Word Document", Ext: ".docx"},
		{ID: "epub", Name: "Open eBook Publication Standard", Ext: ".epub"},
		{ID: "pdfa", Name: "Accessible PDF/A Document", Ext: ".pdf"},
		{ID: "rag_json", Name: "Vector RAG Chunk JSON", Ext: ".json"},
	}
}

func Render(st *state.AppState, selectedIdx int) string {
	var b strings.Builder
	b.WriteString(styles.HeaderStyle.Render(" Multi-Format Exporter Studio ") + "\n\n")

	if st.ActiveDocumentPath == "" {
		b.WriteString(styles.NormalItemStyle.Render("No active document available for export. Process a document first.") + "\n\n")
	} else {
		b.WriteString(styles.ActiveItemStyle.Render(fmt.Sprintf("Active Document: %s", st.ActiveDocumentName)) + "\n")
		b.WriteString(styles.NormalItemStyle.Render(fmt.Sprintf("Target Output Dir: %s", st.ExportOutputDir)) + "\n\n")
	}

	formats := GetSupportedFormats()
	for i, fmtOpt := range formats {
		activeTag := "[ ]"
		if strings.EqualFold(fmtOpt.ID, st.ExportFormat) {
			activeTag = "[✓]"
		}

		line := fmt.Sprintf("%s %-12s | %-35s (%s)", activeTag, fmtOpt.ID, fmtOpt.Name, fmtOpt.Ext)
		if i == selectedIdx {
			b.WriteString(styles.ActiveItemStyle.Render("› "+line) + "\n")
		} else {
			b.WriteString(styles.NormalItemStyle.Render("  "+line) + "\n")
		}
	}

	b.WriteString("\n" + styles.FooterStyle.Render("Space/Enter: select format & trigger export | Esc: Home"))
	return styles.PanelStyle.Render(b.String())
}
