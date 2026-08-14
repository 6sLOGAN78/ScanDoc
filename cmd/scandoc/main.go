package main

import (
	"fmt"
	"os"

	tea "github.com/charmbracelet/bubbletea"

	"scandoc/internal/tui/app"
	"scandoc/internal/tui/backend"
	"scandoc/internal/tui/controller"
	"scandoc/internal/tui/logger"
	"scandoc/internal/tui/state"
)

func main() {
	if err := logger.Init(); err != nil {
		fmt.Fprintf(os.Stderr, "Warning: Failed to init logger: %v\n", err)
	}
	defer logger.Close()

	logger.LogAction("APP_START", "scanDOC TUI started")
	
	st := state.NewAppState()
	services := backend.NewMockServices()
	ctrl := controller.NewController(st, services)
	mainModel := app.NewMainModel(ctrl)

	p := tea.NewProgram(mainModel, tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		logger.LogEvent("ERROR", fmt.Sprintf("Error running scanDOC TUI: %v", err))
		fmt.Fprintf(os.Stderr, "Error running scanDOC TUI: %v\n", err)
		os.Exit(1)
	}
	logger.LogAction("APP_EXIT", "scanDOC TUI exited cleanly")
}
