package settings

import (
	"fmt"
	"strings"

	"scandoc/internal/tui/state"
	"scandoc/internal/tui/styles"
)

func Render(st *state.AppState, selectedIdx int) string {
	var b strings.Builder
	b.WriteString(styles.HeaderStyle.Render(" System Settings & Device Control ") + "\n\n")

	options := []struct {
		Label string
		Value string
		Tree  bool
	}{
		{"Routing Path (Processing Strategy)", strings.ToUpper(st.PipelineConfig.RoutingMode), false},
		{"Air-Gapped Offline Mode (SCANDOC_OFFLINE)", fmt.Sprintf("%v", st.IsOffline()), false},
		{"Hardware Execution Device", strings.ToUpper(st.DeviceType), false},
		{"Quantization & Precision Mode", strings.ToUpper(st.PrecisionMode), false},
		{"Backup Local Data to System (~/.scandoc)", "[PRESS ENTER]", false},
		{"Restore Local Data from System (~/.scandoc)", "[PRESS ENTER]", false},
	}

	for i, opt := range options {
		label := opt.Label
		val := opt.Value
		
		if i == selectedIdx {
			b.WriteString(styles.ActiveItemStyle.Render(fmt.Sprintf("› %-44s : %s", label, val)) + "\n")
		} else {
			if opt.Tree {
				b.WriteString(styles.NormalItemStyle.Render(fmt.Sprintf("  %-44s : %s", label, val)) + "\n")
			} else {
				b.WriteString(styles.NormalItemStyle.Render(fmt.Sprintf("  %-44s : %s", label, val)) + "\n")
			}
		}
	}

	b.WriteString("\n" + styles.FooterStyle.Render("Press Space/Enter to toggle selected setting | Esc to return Home"))
	return styles.PanelStyle.Render(b.String())
}
