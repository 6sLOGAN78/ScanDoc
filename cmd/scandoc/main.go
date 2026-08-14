package main

import (
	"fmt"
	"os"

	tea "github.com/charmbracelet/bubbletea"

	"scandoc/internal/tui/app"
	"scandoc/internal/tui/backend"
	"scandoc/internal/tui/controller"
	"scandoc/internal/tui/state"
)

func main() {
	st := state.NewAppState()
	services := backend.NewMockServices()
	ctrl := controller.NewController(st, services)
	mainModel := app.NewMainModel(ctrl)

	p := tea.NewProgram(mainModel, tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "Error running scanDOC TUI: %v\n", err)
		os.Exit(1)
	}
}
