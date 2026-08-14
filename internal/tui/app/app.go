package app

import (
	"context"
	"path/filepath"
	"strings"

	tea "github.com/charmbracelet/bubbletea"

	"scandoc/internal/tui/backend"
	"scandoc/internal/tui/commands"
	"scandoc/internal/tui/controller"
	"scandoc/internal/tui/events"
	"scandoc/internal/tui/screens/benchmark"
	"scandoc/internal/tui/screens/commandpalette"
	"scandoc/internal/tui/screens/document"
	"scandoc/internal/tui/screens/export"
	"scandoc/internal/tui/screens/filepicker"
	"scandoc/internal/tui/screens/help"
	"scandoc/internal/tui/screens/home"
	"scandoc/internal/tui/screens/models"
	"scandoc/internal/tui/screens/pipeline"
	"scandoc/internal/tui/screens/processing"
	"scandoc/internal/tui/screens/server"
	"scandoc/internal/tui/screens/settings"
	"scandoc/internal/tui/state"
)

type MainModel struct {
	State            *state.AppState
	Controller       *controller.Controller
	Commands         *commands.CommandRegistry
	Width            int
	Height           int
	SelectedIndex    int
	FileItems        []controller.FileItem
	ModelList        []backend.ModelInfo
	BenchmarkResults map[string]any
	IsBenchmarking   bool
}

func NewMainModel(ctrl *controller.Controller) *MainModel {
	if ctrl == nil {
		ctrl = controller.NewController(state.NewAppState(), backend.NewMockServices())
	}
	m := &MainModel{
		State:            ctrl.State,
		Controller:       ctrl,
		Commands:         commands.DefaultCommandRegistry,
		SelectedIndex:    0,
		BenchmarkResults: make(map[string]any),
	}
	m.refreshFileItems()
	m.refreshModelList()
	return m
}

func (m *MainModel) refreshFileItems() {
	items, err := m.Controller.ListDirectoryFiles(m.State.CurrentDir)
	if err == nil {
		m.FileItems = items
	}
}

func (m *MainModel) refreshModelList() {
	list, err := m.Controller.Services.Model.ListModels(context.Background())
	if err == nil {
		m.ModelList = list
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
		m.State.WindowWidth = msg.Width
		m.State.WindowHeight = msg.Height
		return m, nil

	case events.AppEventMsg:
		m.State.AddLog(msg.Message)
		return m, nil

	case tea.KeyMsg:
		k := msg.String()

		// Global Shortcuts
		if k == "ctrl+c" {
			return m, tea.Quit
		}
		if k == "ctrl+p" || k == ">" {
			m.State.NavigateTo(state.ScreenCommandPalette)
			m.SelectedIndex = 0
			return m, nil
		}
		if k == "esc" {
			if m.State.CurrentScreen == state.ScreenHome {
				return m, tea.Quit
			}
			m.State.NavigateTo(state.ScreenHome)
			m.SelectedIndex = 0
			return m, nil
		}

		// Screen-Specific Key Handling
		switch m.State.CurrentScreen {
		case state.ScreenHome:
			items := home.GetMenuItems()
			switch k {
			case "up", "w", "k":
				if m.SelectedIndex > 0 {
					m.SelectedIndex--
				}
			case "down", "s", "j":
				if m.SelectedIndex < len(items)-1 {
					m.SelectedIndex++
				}
			case "enter", "space":
				target := items[m.SelectedIndex].TargetScreen
				if target == "" {
					return m, tea.Quit
				}
				m.State.NavigateTo(target)
				m.SelectedIndex = 0
				m.refreshFileItems()
			case "1":
				m.State.NavigateTo(state.ScreenFilePicker)
				m.SelectedIndex = 0
				m.refreshFileItems()
			case "2":
				m.State.NavigateTo(state.ScreenFolderPicker)
				m.SelectedIndex = 0
				m.refreshFileItems()
			case "3":
				m.State.NavigateTo(state.ScreenDocumentInspector)
				m.SelectedIndex = 0
			case "4":
				m.State.NavigateTo(state.ScreenModelManager)
				m.SelectedIndex = 0
				m.refreshModelList()
			case "5":
				m.State.NavigateTo(state.ScreenPipelineConfig)
				m.SelectedIndex = 0
			case "6":
				m.State.NavigateTo(state.ScreenBenchmark)
				m.SelectedIndex = 0
			case "7":
				m.State.NavigateTo(state.ScreenServerManager)
				m.SelectedIndex = 0
			case "8":
				m.State.NavigateTo(state.ScreenSettings)
				m.SelectedIndex = 0
			case "9":
				m.State.NavigateTo(state.ScreenHelp)
				m.SelectedIndex = 0
			case "q", "0":
				return m, tea.Quit
			}

		case state.ScreenFilePicker, state.ScreenFolderPicker:
			switch k {
			case "up", "w", "k":
				if m.SelectedIndex > 0 {
					m.SelectedIndex--
				}
			case "down", "s", "j":
				if m.SelectedIndex < len(m.FileItems)-1 {
					m.SelectedIndex++
				}
			case "space":
				if len(m.FileItems) > 0 {
					p := m.FileItems[m.SelectedIndex].Path
					m.State.SelectedPaths = append(m.State.SelectedPaths, p)
				}
			case "enter":
				if len(m.State.SelectedPaths) > 0 {
					m.Controller.StartProcessing(context.Background(), m.State.SelectedPaths)
					m.State.NavigateTo(state.ScreenProcessing)
				} else if len(m.FileItems) > 0 {
					item := m.FileItems[m.SelectedIndex]
					if item.IsDir {
						m.State.CurrentDir = item.Path
						m.refreshFileItems()
						m.SelectedIndex = 0
					} else {
						m.State.SelectedPaths = []string{item.Path}
						m.Controller.StartProcessing(context.Background(), m.State.SelectedPaths)
						m.State.NavigateTo(state.ScreenProcessing)
					}
				}
			case "b", "backspace":
				parent := filepath.Dir(m.State.CurrentDir)
				m.State.CurrentDir = parent
				m.refreshFileItems()
				m.SelectedIndex = 0
			}

		case state.ScreenPipelineConfig:
			switch k {
			case "up", "w", "k":
				if m.SelectedIndex > 0 {
					m.SelectedIndex--
				}
			case "down", "s", "j":
				if m.SelectedIndex < 5 {
					m.SelectedIndex++
				}
			case "space", "enter":
				switch m.SelectedIndex {
				case 0:
					m.State.PipelineConfig.EnableOCR = !m.State.PipelineConfig.EnableOCR
				case 1:
					m.State.PipelineConfig.EnableLayout = !m.State.PipelineConfig.EnableLayout
				case 2:
					m.State.PipelineConfig.EnableTable = !m.State.PipelineConfig.EnableTable
				case 3:
					m.State.PipelineConfig.EnableFormula = !m.State.PipelineConfig.EnableFormula
				case 4:
					m.State.PipelineConfig.EnableVLM = !m.State.PipelineConfig.EnableVLM
				case 5:
					m.State.PipelineConfig.EnableVLMFallback = !m.State.PipelineConfig.EnableVLMFallback
				}
			case "r":
				modes := []string{"adaptive", "fast", "deep", "fallback"}
				for idx, mode := range modes {
					if mode == m.State.PipelineConfig.RoutingMode {
						m.State.PipelineConfig.RoutingMode = modes[(idx+1)%len(modes)]
						break
					}
				}
			}

		case state.ScreenModelManager:
			switch k {
			case "up", "w", "k":
				if m.SelectedIndex > 0 {
					m.SelectedIndex--
				}
			case "down", "s", "j":
				if m.SelectedIndex < len(m.ModelList)-1 {
					m.SelectedIndex++
				}
			case "d":
				if len(m.ModelList) > 0 {
					id := m.ModelList[m.SelectedIndex].ModelID
					m.Controller.Services.Model.DownloadModel(context.Background(), id)
					m.refreshModelList()
				}
			case "c":
				if len(m.ModelList) > 0 {
					id := m.ModelList[m.SelectedIndex].ModelID
					m.Controller.Services.Model.ClearCache(context.Background(), id)
					m.refreshModelList()
				}
			}

		case state.ScreenSettings:
			switch k {
			case "up", "w", "k":
				if m.SelectedIndex > 0 {
					m.SelectedIndex--
				}
			case "down", "s", "j":
				if m.SelectedIndex < 3 {
					m.SelectedIndex++
				}
			case "space", "enter":
				switch m.SelectedIndex {
				case 0:
					m.State.ToggleOfflineMode()
				case 1:
					devs := []string{"cpu", "cuda", "openvino"}
					for idx, d := range devs {
						if strings.EqualFold(d, m.State.DeviceType) {
							m.State.DeviceType = devs[(idx+1)%len(devs)]
							break
						}
					}
				case 2:
					precs := []string{"fp32", "fp16", "int8"}
					for idx, p := range precs {
						if strings.EqualFold(p, m.State.PrecisionMode) {
							m.State.PrecisionMode = precs[(idx+1)%len(precs)]
							break
						}
					}
				}
			}

		case state.ScreenBenchmark:
			switch k {
			case "r", "enter":
				m.IsBenchmarking = true
				res, err := m.Controller.Services.Bench.RunBenchmark(context.Background())
				if err == nil {
					m.BenchmarkResults = res
				}
				m.IsBenchmarking = false
			}

		case state.ScreenExport:
			supported := export.GetSupportedFormats()
			switch k {
			case "up", "w", "k":
				if m.SelectedIndex > 0 {
					m.SelectedIndex--
				}
			case "down", "s", "j":
				if m.SelectedIndex < len(supported)-1 {
					m.SelectedIndex++
				}
			case "space", "enter":
				if len(supported) > 0 {
					m.State.ExportFormat = supported[m.SelectedIndex].ID
					if m.State.ActiveDocumentPath != "" {
						m.Controller.Services.Document.Export(context.Background(), m.State.ActiveDocumentPath, m.State.ExportFormat, m.State.ExportOutputDir)
					}
				}
			}

		case state.ScreenServerManager:
			switch k {
			case "s", "enter":
				if m.State.ServerRunning {
					m.Controller.Services.Server.StopServer(context.Background())
					m.State.ServerRunning = false
				} else {
					m.Controller.Services.Server.StartServer(context.Background(), m.State.ServerHost, m.State.ServerPort)
					m.State.ServerRunning = true
				}
			}

		case state.ScreenCommandPalette:
			cmds := commands.DefaultCommandRegistry.ListCommands(m.State.SearchQuery)
			switch k {
			case "up", "w", "k":
				if m.SelectedIndex > 0 {
					m.SelectedIndex--
				}
			case "down", "s", "j":
				if m.SelectedIndex < len(cmds)-1 {
					m.SelectedIndex++
				}
			case "backspace":
				if len(m.State.SearchQuery) > 0 {
					m.State.SearchQuery = m.State.SearchQuery[:len(m.State.SearchQuery)-1]
				}
			case "enter":
				if len(cmds) > 0 {
					target := cmds[m.SelectedIndex].TargetScreen
					if target != "" {
						m.State.NavigateTo(target)
						m.SelectedIndex = 0
						m.State.SearchQuery = ""
					}
				}
			default:
				if len(k) == 1 && k >= " " && k <= "~" {
					m.State.SearchQuery += k
				}
			}
		}
	}

	return m, nil
}

func (m *MainModel) View() string {
	switch m.State.CurrentScreen {
	case state.ScreenHome:
		return home.Render(m.State, m.SelectedIndex)
	case state.ScreenFilePicker, state.ScreenFolderPicker:
		return filepicker.Render(m.State, m.FileItems, m.SelectedIndex)
	case state.ScreenPipelineConfig:
		return pipeline.Render(m.State, m.SelectedIndex)
	case state.ScreenProcessing:
		return processing.Render(m.State)
	case state.ScreenDocumentInspector:
		return document.Render(m.State, m.SelectedIndex)
	case state.ScreenModelManager:
		return models.Render(m.State, m.ModelList, m.SelectedIndex)
	case state.ScreenBenchmark:
		return benchmark.Render(m.State, m.BenchmarkResults, m.IsBenchmarking)
	case state.ScreenExport:
		return export.Render(m.State, m.SelectedIndex)
	case state.ScreenServerManager:
		return server.Render(m.State)
	case state.ScreenSettings:
		return settings.Render(m.State, m.SelectedIndex)
	case state.ScreenHelp:
		return help.Render(m.State)
	case state.ScreenCommandPalette:
		return commandpalette.Render(m.State, m.SelectedIndex)
	default:
		return home.Render(m.State, m.SelectedIndex)
	}
}
