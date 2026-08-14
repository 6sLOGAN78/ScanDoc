package home

import (
	"fmt"
	"strings"

	"scandoc/internal/tui/state"
	"scandoc/internal/tui/styles"
)

type MenuItem struct {
	Key          string
	Title        string
	TargetScreen string
}

func GetMenuItems() []MenuItem {
	return []MenuItem{
		{Key: "1", Title: "Open File", TargetScreen: state.ScreenFilePicker},
		{Key: "2", Title: "Open Folder", TargetScreen: state.ScreenFolderPicker},
		{Key: "3", Title: "Document Inspector", TargetScreen: state.ScreenDocumentInspector},
		{Key: "4", Title: "Model Manager", TargetScreen: state.ScreenModelManager},
		{Key: "5", Title: "Pipeline Configuration", TargetScreen: state.ScreenPipelineConfig},
		{Key: "6", Title: "Benchmark", TargetScreen: state.ScreenBenchmark},
		{Key: "7", Title: "Server", TargetScreen: state.ScreenServerManager},
		{Key: "8", Title: "Settings", TargetScreen: state.ScreenSettings},
		{Key: "9", Title: "Help", TargetScreen: state.ScreenHelp},
		{Key: "Q", Title: "Quit", TargetScreen: ""},
	}
}

func Render(st *state.AppState, selectedIdx int) string {
	items := GetMenuItems()

	var b strings.Builder
	b.WriteString(styles.HeaderStyle.Render(" scanDOC Document Intelligence Engine v0.1.0 ") + "\n\n")

	for i, item := range items {
		if i == selectedIdx {
			b.WriteString(styles.ActiveItemStyle.Render(fmt.Sprintf("[%s]  › %-35s", item.Key, item.Title)) + "\n")
		} else {
			b.WriteString(styles.NormalItemStyle.Render(fmt.Sprintf("[%s]    %-35s", item.Key, item.Title)) + "\n")
		}
	}

	b.WriteString("\n")

	offlineBadge := styles.BadgeGreen.Render("● ONLINE READY")
	if st.IsOffline() {
		offlineBadge = styles.BadgeAmber.Render("● AIR-GAPPED OFFLINE")
	}

	deviceInfo := fmt.Sprintf("Local • %s • Device: %s", offlineBadge, strings.ToUpper(st.DeviceType))
	footer := styles.FooterStyle.Render(deviceInfo)
	b.WriteString(footer + "\n")

	return styles.PanelStyle.Render(b.String())
}
