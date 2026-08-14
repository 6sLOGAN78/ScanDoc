package server

import (
	"fmt"
	"strings"

	"scandoc/internal/tui/state"
	"scandoc/internal/tui/styles"
)

func Render(st *state.AppState) string {
	var b strings.Builder
	b.WriteString(styles.HeaderStyle.Render(" REST API & Visual Studio Web Server Control ") + "\n\n")

	if st.ServerRunning {
		b.WriteString(styles.BadgeSuccess.Render(fmt.Sprintf("● SERVER ACTIVE: Running on http://%s:%d", st.ServerHost, st.ServerPort)) + "\n\n")
		b.WriteString(styles.ActiveItemStyle.Render(fmt.Sprintf("OpenAPI Specs : http://%s:%d/docs", st.ServerHost, st.ServerPort)) + "\n")
		b.WriteString(styles.ActiveItemStyle.Render(fmt.Sprintf("Visual Studio : http://%s:%d/studio", st.ServerHost, st.ServerPort)) + "\n\n")
	} else {
		b.WriteString(styles.BadgeWarning.Render("○ SERVER STOPPED: Press 's' or Enter to start background server") + "\n\n")
		b.WriteString(styles.NormalItemStyle.Render(fmt.Sprintf("Configured Host : %s", st.ServerHost)) + "\n")
		b.WriteString(styles.NormalItemStyle.Render(fmt.Sprintf("Configured Port : %d", st.ServerPort)) + "\n\n")
	}

	b.WriteString("\n" + styles.FooterStyle.Render("s / Enter: toggle server state (start/stop) | Esc: Home"))
	return styles.PanelStyle.Render(b.String())
}
