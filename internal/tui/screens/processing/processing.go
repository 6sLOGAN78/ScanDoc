package processing

import (
	"fmt"
	"strings"

	"scandoc/internal/tui/state"
	"scandoc/internal/tui/styles"
)

func Render(st *state.AppState) string {
	var b strings.Builder
	b.WriteString(styles.HeaderStyle.Render(" Pipeline Processing Monitor ") + "\n\n")

	b.WriteString(styles.ActiveItemStyle.Render(fmt.Sprintf("Status : %s", strings.ToUpper(st.ProcessingStatus))) + "\n")
	b.WriteString(styles.NormalItemStyle.Render(fmt.Sprintf("Stage  : %s", st.ProgressStage)) + "\n\n")

	// Render Progress Bar
	barLen := 40
	filled := int(float64(barLen) * st.ProgressPct / 100.0)
	if filled > barLen {
		filled = barLen
	}
	bar := strings.Repeat("=", filled) + strings.Repeat("-", barLen-filled)
	b.WriteString(styles.ActiveItemStyle.Render(fmt.Sprintf("[%s] %5.1f%%", bar, st.ProgressPct)) + "\n\n")

	if len(st.ProcessingErrors) > 0 {
		b.WriteString(styles.HeaderStyle.Render(" Errors ") + "\n")
		for _, errStr := range st.ProcessingErrors {
			b.WriteString(styles.NormalItemStyle.Render("❌ "+errStr) + "\n")
		}
		b.WriteString("\n")
	}

	b.WriteString(styles.HeaderStyle.Render(" Recent Telemetry Logs ") + "\n")
	logStart := 0
	if len(st.ProcessingLogs) > 8 {
		logStart = len(st.ProcessingLogs) - 8
	}
	for _, logLine := range st.ProcessingLogs[logStart:] {
		b.WriteString(styles.NormalItemStyle.Render("• "+logLine) + "\n")
	}

	b.WriteString("\n" + styles.FooterStyle.Render("Press Esc or Enter to return to Home Dashboard | Esc cancels pipeline"))
	return styles.PanelStyle.Render(b.String())
}
