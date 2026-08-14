package processing

import (
	"fmt"
	"strings"

	"scandoc/internal/tui/state"
	"scandoc/internal/tui/styles"
)

var pipelineStages = []string{
	"Parse",
	"Extract",
	"Preprocess",
	"OCR",
	"Layout",
	"Tables",
	"Figures",
	"Chunk",
	"Index",
}

func Render(st *state.AppState) string {
	var b strings.Builder
	
	docName := st.ActiveDocumentName
	if docName == "" {
		docName = "document"
	}

	b.WriteString(styles.TitleStyle.Render(fmt.Sprintf("Processing %s", docName)) + "\n\n")

	// Current Stage Header
	stage := st.ProgressStage
	if stage == "" {
		stage = "Initializing"
	}
	b.WriteString(styles.SectionStyle.Render(strings.ToUpper(stage)) + "\n\n")

	// Page info & Progress Bar
	if st.TotalPages > 0 {
		b.WriteString(styles.NormalItemStyle.Render(fmt.Sprintf("Page %d / %d", st.CurrentPage, st.TotalPages)) + "\n")
	}

	barLen := 30
	filled := int(float64(barLen) * st.ProgressPct / 100.0)
	if filled > barLen {
		filled = barLen
	}
	bar := strings.Repeat("█", filled) + strings.Repeat("░", barLen-filled)
	
	b.WriteString(styles.PrimaryStyle.Render(fmt.Sprintf("%s  %d%%", bar, int(st.ProgressPct))) + "\n\n")

	// Pipeline visualization
	b.WriteString(styles.SectionStyle.Render("Pipeline") + "\n\n")
	
	currentIdx := -1
	for i, s := range pipelineStages {
		if strings.EqualFold(s, st.ProgressStage) {
			currentIdx = i
			break
		}
	}
	
	if st.ProcessingStatus == "completed" {
		currentIdx = len(pipelineStages)
	}

	for i, s := range pipelineStages {
		prefix := "○"
		style := styles.MutedStyle
		
		if i < currentIdx {
			prefix = "✓"
			style = styles.BadgeSuccess
		} else if i == currentIdx {
			prefix = "●"
			style = styles.PrimaryStyle
		}
		
		if st.ProcessingStatus == "failed" && i == currentIdx {
			prefix = "✕"
			style = styles.BadgeError
		}

		b.WriteString(style.Render(fmt.Sprintf("  %s %s", prefix, s)) + "\n")
	}
	b.WriteString("\n")

	// Logs
	if len(st.ProcessingErrors) > 0 {
		b.WriteString(styles.SectionStyle.Render("Errors") + "\n\n")
		for _, errStr := range st.ProcessingErrors {
			b.WriteString(styles.BadgeError.Render("  ! "+errStr) + "\n")
		}
		b.WriteString("\n")
	}

	sepWidth := st.WindowWidth - 25
	if sepWidth < 10 {
		sepWidth = 50
	}
	
	b.WriteString(styles.MutedStyle.Render(strings.Repeat("─", sepWidth)) + "\n")
	b.WriteString(styles.FooterStyle.Render("c Cancel   p Pause   l Logs   Esc Back"))
	return b.String()
}
