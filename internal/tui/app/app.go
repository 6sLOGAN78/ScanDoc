package app

import (
	"context"
	"fmt"
	"path/filepath"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"

	"scandoc/internal/tui/backend"
	"scandoc/internal/tui/commands"
	"scandoc/internal/tui/controller"
	"scandoc/internal/tui/events"
	"scandoc/internal/tui/logger"
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
	"scandoc/internal/tui/styles"
)

type FocusPanel int

const (
	FocusSidebar FocusPanel = iota
	FocusContent
)

type SidebarItem struct {
	Title  string
	Screen string
}

type SidebarGroup struct {
	Title string
	Items []SidebarItem
}

var SidebarData = []SidebarGroup{
	{
		Title: "WORKSPACE",
		Items: []SidebarItem{
			{"Dashboard", state.ScreenHome},
			{"Documents", state.ScreenFilePicker},
			{"Outputs", state.ScreenOutputs},
			{"Jobs", state.ScreenProcessing},
			{"Inspector", state.ScreenDocumentInspector},
			{"Export", state.ScreenExport},
		},
	},
	{
		Title: "SYSTEM",
		Items: []SidebarItem{
			{"Models", state.ScreenModelManager},
			{"Pipeline", state.ScreenPipelineConfig},
			{"Benchmark", state.ScreenBenchmark},
			{"Server", state.ScreenServerManager},
			{"Settings", state.ScreenSettings},
			{"Help", state.ScreenHelp},
		},
	},
}

type MainModel struct {
	State            *state.AppState
	Controller       *controller.Controller
	Commands         *commands.CommandRegistry
	Width            int
	Height           int
	SelectedIndex    int
	FileItems        []controller.FileItem
	WorkspaceItems   []controller.FileItem
	ModelList        []backend.ModelInfo
	BenchmarkResults map[string]any
	IsBenchmarking   bool

	FocusedPanel FocusPanel
	SidebarIndex int // flatted index
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
		FocusedPanel:     FocusSidebar, // default focus sidebar for immediate navigation
		SidebarIndex:     0,
	}
	m.refreshFileItems()
	m.refreshWorkspaceItems()
	m.refreshModelList()
	return m
}

func (m *MainModel) refreshFileItems() {
	items, err := m.Controller.ListDirectoryFiles(m.State.CurrentDir)
	if err == nil {
		m.FileItems = items
	}
}

func (m *MainModel) refreshWorkspaceItems() {
	items, err := m.Controller.ListDirectoryFiles(m.State.WorkspaceDir)
	if err == nil {
		m.WorkspaceItems = items
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

func (m *MainModel) getFlatSidebar() []SidebarItem {
	var items []SidebarItem
	for _, g := range SidebarData {
		items = append(items, g.Items...)
	}
	return items
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
		logger.LogKeyPress(k, string(m.State.CurrentScreen))

		// Global Shortcuts
		if k == "ctrl+c" {
			return m, tea.Quit
		}
		if k == "ctrl+p" {
			m.State.NavigateTo(state.ScreenCommandPalette)
			m.SelectedIndex = 0
			m.FocusedPanel = FocusContent
			return m, nil
		}
		
		// Focus toggle
		if k == "tab" && m.State.CurrentScreen != state.ScreenCommandPalette {
			if m.FocusedPanel == FocusSidebar {
				m.FocusedPanel = FocusContent
			} else {
				m.FocusedPanel = FocusSidebar
				// synchronize sidebar index with current screen
				flat := m.getFlatSidebar()
				for i, item := range flat {
					if item.Screen == m.State.CurrentScreen {
						m.SidebarIndex = i
						break
					}
				}
			}
			return m, nil
		}

		if m.FocusedPanel == FocusSidebar {
			flat := m.getFlatSidebar()
			switch k {
			case "up", "k":
				if m.SidebarIndex > 0 {
					m.SidebarIndex--
				}
			case "down", "j":
				if m.SidebarIndex < len(flat)-1 {
					m.SidebarIndex++
				}
			case "enter", " ":
				target := flat[m.SidebarIndex].Screen
				m.State.NavigateTo(target)
				m.SelectedIndex = 0
				m.FocusedPanel = FocusContent
				if target == state.ScreenFilePicker || target == state.ScreenFolderPicker {
					m.refreshFileItems()
				}
				if target == state.ScreenOutputs {
					m.refreshWorkspaceItems()
				}
				if target == state.ScreenModelManager {
					m.refreshModelList()
				}
			case "l", "right":
				m.FocusedPanel = FocusContent
			case "q":
				return m, tea.Quit
			}
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

		if (k == "left" || k == "h") && m.FocusedPanel == FocusContent {
			if m.State.CurrentScreen != state.ScreenCommandPalette {
				m.FocusedPanel = FocusSidebar
				return m, nil
			}
		}

		// Content Navigation
		switch m.State.CurrentScreen {
		case state.ScreenHome:
			switch k {
			case "q":
				return m, tea.Quit
			}
			// Home is now mostly static dashboard

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
			case "pgup":
				step := m.State.WindowHeight - 12
				if step < 5 { step = 10 }
				m.SelectedIndex -= step
				if m.SelectedIndex < 0 { m.SelectedIndex = 0 }
			case "pgdown":
				step := m.State.WindowHeight - 12
				if step < 5 { step = 10 }
				m.SelectedIndex += step
				if m.SelectedIndex >= len(m.FileItems) {
					m.SelectedIndex = len(m.FileItems) - 1
					if m.SelectedIndex < 0 { m.SelectedIndex = 0 }
				}
			case " ":
				if len(m.FileItems) > 0 {
					p := m.FileItems[m.SelectedIndex].Path
					found := -1
					for i, sp := range m.State.SelectedPaths {
						if sp == p {
							found = i
							break
						}
					}
					if found >= 0 {
						m.State.SelectedPaths = append(m.State.SelectedPaths[:found], m.State.SelectedPaths[found+1:]...)
					} else {
						m.State.SelectedPaths = append(m.State.SelectedPaths, p)
					}
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

		case state.ScreenOutputs:
			switch k {
			case "up", "w", "k":
				if m.SelectedIndex > 0 {
					m.SelectedIndex--
				}
			case "down", "s", "j":
				if m.SelectedIndex < len(m.WorkspaceItems)-1 {
					m.SelectedIndex++
				}
			case "pgup":
				step := m.State.WindowHeight - 12
				if step < 5 { step = 10 }
				m.SelectedIndex -= step
				if m.SelectedIndex < 0 { m.SelectedIndex = 0 }
			case "pgdown":
				step := m.State.WindowHeight - 12
				if step < 5 { step = 10 }
				m.SelectedIndex += step
				if m.SelectedIndex >= len(m.WorkspaceItems) {
					m.SelectedIndex = len(m.WorkspaceItems) - 1
					if m.SelectedIndex < 0 { m.SelectedIndex = 0 }
				}
			case "enter":
				if len(m.WorkspaceItems) > 0 {
					item := m.WorkspaceItems[m.SelectedIndex]
					if item.IsDir {
						m.State.WorkspaceDir = item.Path
						m.refreshWorkspaceItems()
						m.SelectedIndex = 0
					}
				}
			case "b", "backspace":
				parent := filepath.Dir(m.State.WorkspaceDir)
				if strings.HasPrefix(filepath.Clean(parent), filepath.Clean(m.State.WorkspaceRoot)) {
					m.State.WorkspaceDir = parent
					m.refreshWorkspaceItems()
					m.SelectedIndex = 0
				}
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
			case " ", "enter":
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
			case " ", "enter":
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

		case state.ScreenDocumentInspector:
			switch k {
			case "up", "w", "k":
				if m.SelectedIndex > 0 {
					m.SelectedIndex--
				}
			case "down", "s", "j":
				if m.SelectedIndex < 3 {
					m.SelectedIndex++
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
			case " ", "enter":
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
				if len(cmds) > 0 && m.SelectedIndex < len(cmds) {
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

func (m *MainModel) renderSidebar() string {
	var b strings.Builder
	
	// App Title
	b.WriteString(styles.TitleStyle.Render("scanDOC") + "\n\n")

	flatIdx := 0
	for _, group := range SidebarData {
		b.WriteString(styles.SectionStyle.Render(group.Title) + "\n")
		for _, item := range group.Items {
			prefix := "  "
			if m.FocusedPanel == FocusSidebar && flatIdx == m.SidebarIndex {
				prefix = "> "
				b.WriteString(styles.SelectedItemStyle.Render(fmt.Sprintf("%s%-14s", prefix, item.Title)) + "\n")
			} else if item.Screen == m.State.CurrentScreen {
				// highlight current screen if sidebar not focused
				b.WriteString(styles.PrimaryStyle.Render(fmt.Sprintf("  %-14s", item.Title)) + "\n")
			} else {
				b.WriteString(styles.NormalItemStyle.Render(fmt.Sprintf("  %-14s", item.Title)) + "\n")
			}
			flatIdx++
		}
		b.WriteString("\n")
	}

	b.WriteString(styles.MutedStyle.Render(strings.Repeat("─", 16)) + "\n")
	b.WriteString(styles.SecondaryStyle.Render("project-name") + "\n")
	b.WriteString(styles.MutedStyle.Render(strings.Repeat("─", 16)) + "\n\n")
	b.WriteString(styles.MutedStyle.Render("? Help\nq Quit"))

	style := styles.SidebarStyle
	if m.FocusedPanel == FocusSidebar {
		style = styles.SidebarFocusedStyle
	}

	// Fix sidebar height if possible
	return style.Height(m.Height - 2).Render(b.String())
}

func (m *MainModel) View() string {
	if m.Width < 20 || m.Height < 10 {
		return "Terminal too small"
	}

	var mainContent string
	switch m.State.CurrentScreen {
	case state.ScreenHome:
		mainContent = home.Render(m.State, m.SelectedIndex)
	case state.ScreenFilePicker, state.ScreenFolderPicker:
		mainContent = filepicker.Render(m.State, m.FileItems, m.SelectedIndex, m.State.CurrentDir)
	case state.ScreenOutputs:
		mainContent = filepicker.Render(m.State, m.WorkspaceItems, m.SelectedIndex, "WORKSPACE: "+m.State.WorkspaceDir)
	case state.ScreenPipelineConfig:
		mainContent = pipeline.Render(m.State, m.SelectedIndex)
	case state.ScreenProcessing:
		mainContent = processing.Render(m.State)
	case state.ScreenDocumentInspector:
		mainContent = document.Render(m.State, m.SelectedIndex)
	case state.ScreenModelManager:
		mainContent = models.Render(m.State, m.ModelList, m.SelectedIndex)
	case state.ScreenBenchmark:
		mainContent = benchmark.Render(m.State, m.BenchmarkResults, m.IsBenchmarking)
	case state.ScreenExport:
		mainContent = export.Render(m.State, m.SelectedIndex)
	case state.ScreenServerManager:
		mainContent = server.Render(m.State)
	case state.ScreenSettings:
		mainContent = settings.Render(m.State, m.SelectedIndex)
	case state.ScreenHelp:
		mainContent = help.Render(m.State)
	case state.ScreenCommandPalette:
		mainContent = commandpalette.Render(m.State, m.SelectedIndex)
	default:
		mainContent = home.Render(m.State, m.SelectedIndex)
	}

	mainContent = styles.MainContentStyle.Width(m.Width - 22).Height(m.Height - 2).Render(mainContent)

	layout := lipgloss.JoinHorizontal(lipgloss.Top, m.renderSidebar(), mainContent)
	return layout
}
