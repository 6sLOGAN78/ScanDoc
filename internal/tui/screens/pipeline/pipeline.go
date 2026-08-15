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
		{"Optical Character Recognition (OCR Engine)", st.PipelineConfig.EnableOCR, "RapidOCR PP-OCRv4 ONNX"},
		{"Visual Layout Analysis (Layout Detector)", st.PipelineConfig.EnableLayout, "RT-DETR DocLayNet ONNX"},
		{"Neural Table Structure Recognition", st.PipelineConfig.EnableTable, "SLANet Table ONNX"},
		{"Mathematical Formula LaTeX Parsing", st.PipelineConfig.EnableFormula, "Pix2Text LaTeX-OCR ONNX"},
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

	b.WriteString("\n" + styles.FooterStyle.Render("Space: toggle stage | r: cycle routing mode (adaptive/fast/deep/fallback) | Esc: Home"))
	return styles.PanelStyle.Render(b.String())
}
