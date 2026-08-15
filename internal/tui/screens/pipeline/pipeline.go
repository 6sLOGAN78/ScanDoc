package pipeline

import (
	"fmt"
	"strings"

	"scandoc/internal/tui/state"
	"scandoc/internal/tui/styles"
)

func Render(st *state.AppState, selectedIdx int) string {
	var b strings.Builder
	b.WriteString(styles.HeaderStyle.Render(" Pipeline Stage Configuration & Routing ") + "\n\n")

	b.WriteString(styles.ActiveItemStyle.Render(fmt.Sprintf("Current Agentic Routing Mode: [%s]", strings.ToUpper(st.PipelineConfig.RoutingMode))) + "\n\n")

	stages := []struct {
		Label   string
		Enabled bool
		Desc    string
	}{
		{"Optical Character Recognition (OCR Engine)", st.PipelineConfig.EnableOCR, st.PipelineConfig.OCRModel},
		{"Visual Layout Analysis (Layout Detector)", st.PipelineConfig.EnableLayout, st.PipelineConfig.LayoutModel},
		{"Neural Table Structure Recognition", st.PipelineConfig.EnableTable, st.PipelineConfig.TableModel},
		{"Mathematical Formula LaTeX Parsing", st.PipelineConfig.EnableFormula, st.PipelineConfig.FormulaModel},
	}

	for i, stage := range stages {
		check := "[ ]"
		if stage.Enabled {
			check = "[✓]"
		}

		line := fmt.Sprintf("%s %-45s | %s", check, stage.Label, stage.Desc)
		if i == selectedIdx {
			b.WriteString(styles.ActiveItemStyle.Render("› "+line) + "\n")
		} else {
			b.WriteString(styles.NormalItemStyle.Render("  "+line) + "\n")
		}
	}

	b.WriteString("\n" + styles.FooterStyle.Render("Space: toggle stage | Enter: cycle model | r: cycle routing mode | Esc: Home"))
	return styles.PanelStyle.Render(b.String())
}
