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
	}{
		{"Air-Gapped Offline Mode (SCANDOC_OFFLINE)", fmt.Sprintf("%v", st.IsOffline())},
		{"Hardware Execution Device", strings.ToUpper(st.DeviceType)},
		{"Quantization & Precision Mode", strings.ToUpper(st.PrecisionMode)},
		{"Default Export Output Directory", st.ExportOutputDir},
		{"Backup Local Data to System (~/.scandoc)", "[PRESS ENTER]"},
		{"Restore Local Data from System (~/.scandoc)", "[PRESS ENTER]"},
	}

	for i, opt := range options {
		if i == selectedIdx {
			b.WriteString(styles.ActiveItemStyle.Render(fmt.Sprintf("› %-42s : %s", opt.Label, opt.Value)) + "\n")
		} else {
			b.WriteString(styles.NormalItemStyle.Render(fmt.Sprintf("  %-42s : %s", opt.Label, opt.Value)) + "\n")
		}
	}

	b.WriteString("\n" + styles.FooterStyle.Render("Press Space/Enter to toggle selected setting | Esc to return Home"))
	return styles.PanelStyle.Render(b.String())
}
