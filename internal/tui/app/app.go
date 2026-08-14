package app

import (
	tea "github.com/charmbracelet/bubbletea"

	"scandoc/internal/tui/backend"
	"scandoc/internal/tui/commands"
	"scandoc/internal/tui/controller"
	"scandoc/internal/tui/events"
	"scandoc/internal/tui/state"
)

type MainModel struct {
	State      *state.AppState
	Controller *controller.Controller
	Commands   *commands.CommandRegistry
	Width      int
	Height     int
	ScreenIdx  int
}

func NewMainModel(ctrl *controller.Controller) *MainModel {
	if ctrl == nil {
		ctrl = controller.NewController(state.NewAppState(), backend.NewMockServices())
	}
	return &MainModel{
		State:      ctrl.State,
		Controller: ctrl,
		Commands:   commands.DefaultCommandRegistry,
		ScreenIdx:  0,
	}
}

func (m *MainModel) Init() tea.Cmd {
	return nil
}

func (m *MainModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.Width = msg.Width
		m.Height = msg.Height
		return m, nil

	case events.AppEventMsg:
		m.State.AddLog(msg.Message)
		return m, nil

	case tea.KeyMsg:
		switch msg.String() {
		case "q", "ctrl+c":
			if m.State.CurrentScreen == state.ScreenHome {
				return m, tea.Quit
			}
			m.State.NavigateTo(state.ScreenHome)
			m.ScreenIdx = 0
			return m, nil

		case "esc":
			m.State.NavigateTo(state.ScreenHome)
			m.ScreenIdx = 0
			return m, nil

		case "ctrl+p", ">":
			m.State.NavigateTo(state.ScreenCommandPalette)
			m.ScreenIdx = 0
			return m, nil
		}
	}

	return m, nil
}

func (m *MainModel) View() string {
	return "scanDOC Terminal UI (Native Go)\nScreen: " + m.State.CurrentScreen + "\nPress 'q' to quit."
}
