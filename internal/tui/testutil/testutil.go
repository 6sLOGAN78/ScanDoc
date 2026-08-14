package testutil

import (
	"scandoc/internal/tui/backend"
	"scandoc/internal/tui/controller"
	"scandoc/internal/tui/state"
)

type TestHarness struct {
	State      *state.AppState
	Services   *backend.Services
	Controller *controller.Controller
}

func NewTestHarness() *TestHarness {
	st := state.NewAppState()
	services := backend.NewMockServices()
	ctrl := controller.NewController(st, services)
	return &TestHarness{
		State:      st,
		Services:   services,
		Controller: ctrl,
	}
}
