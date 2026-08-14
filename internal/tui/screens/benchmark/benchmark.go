package benchmark

import (
	"fmt"
	"strings"

	"scandoc/internal/tui/state"
	"scandoc/internal/tui/styles"
)

func Render(st *state.AppState, results map[string]any, isRunning bool) string {
	var b strings.Builder
	b.WriteString(styles.HeaderStyle.Render(" Performance Benchmark Suite (scanDOC vs Docling) ") + "\n\n")

	if isRunning {
		b.WriteString(styles.BadgeWarning.Render("RUNNING BENCHMARK SUITE... Please wait.") + "\n\n")
	} else if len(results) == 0 {
		b.WriteString(styles.NormalItemStyle.Render("No benchmark results yet. Press 'r' or Enter to run the benchmark suite.") + "\n\n")
	} else {
		b.WriteString(styles.BadgeSuccess.Render("BENCHMARK RESULTS COMPLETED") + "\n\n")

		scandocFPS, _ := results["scandoc_fps"].(float64)
		doclingFPS, _ := results["docling_fps"].(float64)
		speedup, _ := results["speedup"].(float64)

		b.WriteString(styles.ActiveItemStyle.Render(fmt.Sprintf("scanDOC Engine Throughput : %.1f pages/sec", scandocFPS)) + "\n")
		b.WriteString(styles.NormalItemStyle.Render(fmt.Sprintf("Docling Engine Throughput : %.1f pages/sec", doclingFPS)) + "\n")
		b.WriteString(styles.ActiveItemStyle.Render(fmt.Sprintf("Relative Speedup Factor   : %.2fx Faster", speedup)) + "\n\n")
	}

	b.WriteString(styles.NormalItemStyle.Render("Configuration: Warmup Rounds: 1 | Benchmark Rounds: 3 | Device: CPU") + "\n")
	b.WriteString("\n" + styles.FooterStyle.Render("r / Enter: run benchmark suite | Esc: Home"))
	return styles.PanelStyle.Render(b.String())
}
