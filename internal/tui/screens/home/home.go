package home

import (
	"fmt"
	"strings"
	"time"

	"scandoc/internal/tui/state"
	"scandoc/internal/tui/styles"
)

func Render(st *state.AppState, selectedIdx int) string {
	var b strings.Builder
	
	// Dashboard Header
	b.WriteString(styles.TitleStyle.Render("Dashboard") + "\n\n")
	
	// System Status
	offlineBadge := styles.BadgeSuccess.Render("✓ ONLINE")
	if st.IsOffline() {
		offlineBadge = styles.BadgeWarning.Render("! AIR-GAPPED")
	}
	
	b.WriteString(styles.SecondaryStyle.Render(fmt.Sprintf("Status: %s   Device: %s   Precision: %s", 
		offlineBadge, 
		strings.ToUpper(st.DeviceType),
		strings.ToUpper(st.PrecisionMode),
	)) + "\n\n")
	
	sepWidth := st.WindowWidth - 25
	if sepWidth < 10 {
		sepWidth = 50
	}
	
	// Recent Documents
	b.WriteString(styles.SectionStyle.Render("Recent") + "\n")
	b.WriteString(styles.MutedStyle.Render(strings.Repeat("─", sepWidth)) + "\n")
	
	if len(st.RecentDocuments) == 0 {
		b.WriteString(styles.MutedStyle.Render("  No recent documents") + "\n")
	} else {
		for i, doc := range st.RecentDocuments {
			if i > 4 {
				break
			}
			age := time.Since(doc.Timestamp).Round(time.Minute)
			statusStr := doc.Status
			if statusStr == "" {
				statusStr = "Ready"
			}
			
			// Format row
			row := fmt.Sprintf("  %-30s %-15s %s", doc.Name, statusStr, age.String()+" ago")
			b.WriteString(styles.NormalItemStyle.Render(row) + "\n")
		}
	}
	b.WriteString("\n")

	// Active Jobs
	b.WriteString(styles.SectionStyle.Render("Active jobs") + "\n")
	b.WriteString(styles.MutedStyle.Render(strings.Repeat("─", sepWidth)) + "\n")
	
	if st.ProcessingStatus == "processing" {
		row := fmt.Sprintf("  %-30s %-15s %d%%", st.ActiveDocumentName, st.ProgressStage, int(st.ProgressPct))
		b.WriteString(styles.NormalItemStyle.Render(row) + "\n")
	} else {
		b.WriteString(styles.MutedStyle.Render("  No active jobs") + "\n")
	}
	b.WriteString("\n")

	// Quick Actions
	b.WriteString(styles.SectionStyle.Render("Quick actions") + "\n")
	b.WriteString(styles.MutedStyle.Render(strings.Repeat("─", sepWidth)) + "\n")
	b.WriteString(styles.NormalItemStyle.Render("  Enter  Navigate workspace"))
	b.WriteString(styles.NormalItemStyle.Render("  Ctrl+P Command palette"))
	b.WriteString(styles.NormalItemStyle.Render("  Tab    Focus sidebar"))
	b.WriteString("\n")

	return b.String()
}
