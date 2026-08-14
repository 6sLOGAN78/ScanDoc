package models

import (
	"fmt"
	"strings"

	"scandoc/internal/tui/backend"
	"scandoc/internal/tui/state"
	"scandoc/internal/tui/styles"
)

func Render(st *state.AppState, modelList []backend.ModelInfo, selectedIdx int) string {
	var b strings.Builder
	b.WriteString(styles.HeaderStyle.Render(" Model Lifecycle & Local Cache Manager ") + "\n\n")

	b.WriteString(styles.NormalItemStyle.Render("Cache Location: ~/.cache/scandoc/models/") + "\n")
	if st.IsOffline() {
		b.WriteString(styles.BadgeAmber.Render("AIR-GAPPED OFFLINE MODE: Network model downloads disabled.") + "\n\n")
	} else {
		b.WriteString(styles.BadgeGreen.Render("ONLINE MODE: Model downloading enabled.") + "\n\n")
	}

	if len(modelList) == 0 {
		b.WriteString(styles.NormalItemStyle.Render("No models registered.") + "\n")
	} else {
		for i, m := range modelList {
			statusTag := "INSTALLED"
			if !m.Installed {
				statusTag = "NOT INSTALLED"
			}

			sizeMB := float64(m.SizeBytes) / (1024 * 1024)
			line := fmt.Sprintf("[%s] %-20s | %-38s | %5.1f MB", statusTag, m.ModelID, m.Name, sizeMB)

			if i == selectedIdx {
				b.WriteString(styles.ActiveItemStyle.Render("› "+line) + "\n")
			} else {
				b.WriteString(styles.NormalItemStyle.Render("  "+line) + "\n")
			}
		}
	}

	b.WriteString("\n" + styles.FooterStyle.Render("d: download model | c: clear cache | Esc: Home"))
	return styles.PanelStyle.Render(b.String())
}
