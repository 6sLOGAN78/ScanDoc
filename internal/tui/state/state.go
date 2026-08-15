package state

import (
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// Screen identifiers matching Python ScreenType
const (
	ScreenHome              = "home"
	ScreenFilePicker        = "file_picker"
	ScreenOutputs           = "outputs"
	ScreenFolderPicker      = "folder_picker"
	ScreenPipelineConfig    = "pipeline_config"
	ScreenProcessing        = "processing"
	ScreenDocumentInspector = "document_inspector"
	ScreenExport            = "export"
	ScreenModelManager      = "model_manager"
	ScreenBenchmark         = "benchmark"
	ScreenServerManager     = "server_manager"
	ScreenSettings          = "settings"
	ScreenHelp              = "help"
	ScreenCommandPalette    = "command_palette"
)

type RecentDocument struct {
	Name      string    `json:"name"`
	Path      string    `json:"path"`
	Status    string    `json:"status"`
	SizeBytes int64     `json:"size_bytes"`
	Timestamp time.Time `json:"timestamp"`
}

type PipelineConfig struct {
	EnableOCR         bool   `json:"enable_ocr"`
	EnableLayout      bool   `json:"enable_layout"`
	EnableTable       bool   `json:"enable_table"`
	EnableFormula     bool   `json:"enable_formula"`
	EnableVLM         bool   `json:"enable_vlm"`
	RoutingMode       string `json:"routing_mode"` // "adaptive", "fast", "deep"
	FastModel         string `json:"fast_model"`
	DeepModel         string `json:"deep_model"`
}

type AppState struct {
	mu sync.RWMutex

	CurrentScreen  string
	PreviousScreen string

	// Navigation & File Selection
	CurrentDir      string
	WorkspaceDir    string
	WorkspaceRoot   string
	SelectedPaths   []string
	WindowWidth     int
	WindowHeight    int
	SearchQuery     string
	TickCount       int
	ExtensionFilter string

	// Active Document & Processing State
	ActiveDocumentPath string
	ActiveDocumentName string
	ProcessingStatus   string // "idle", "processing", "completed", "failed", "cancelled"
	ProgressStage      string
	ProgressPct        float64
	CurrentPage        int
	TotalPages         int
	ProcessingErrors   []string
	ProcessingLogs     []string

	// Pipeline & Device Config
	PipelineConfig PipelineConfig
	OfflineMode    bool
	DeviceType     string // "cpu", "cuda", "openvino"
	PrecisionMode  string // "fp32", "fp16", "int8"

	// Export Configuration
	ExportFormat    string
	ExportOutputDir string
	IncludeImages   bool
	PreserveFormulas bool
	PreserveTables   bool

	// Server Control State
	ServerRunning bool
	ServerHost    string
	ServerPort    int

	// Recent Documents History
	RecentDocuments []RecentDocument
}

func NewAppState() *AppState {
	cwd, err := os.Getwd()
	if err != nil {
		cwd = "."
	}
	return &AppState{
		CurrentScreen:   ScreenHome,
		CurrentDir:      cwd,
		WorkspaceDir:    filepath.Join(cwd, "local", "scandoc", "output"),
		WorkspaceRoot:   filepath.Join(cwd, "local", "scandoc", "output"),
		SelectedPaths:   make([]string, 0),
		ProcessingLogs:  make([]string, 0),
		ProcessingErrors: make([]string, 0),
		PipelineConfig: PipelineConfig{
			EnableOCR:         true,
			EnableLayout:      true,
			EnableTable:       true,
			EnableFormula:     true,
			EnableVLM:         true,
			RoutingMode:       "adaptive",
			FastModel:         "RapidOCR Mobile PP-OCRv4",
			DeepModel:         "RT-DETR DocLayNet",
		},
		OfflineMode:     os.Getenv("SCANDOC_OFFLINE") == "1",
		DeviceType:      "cpu",
		PrecisionMode:   "fp32",
		ExportFormat:    "markdown",
		ExportOutputDir: filepath.Join(cwd, "output"),
		IncludeImages:   true,
		PreserveFormulas: true,
		PreserveTables:   true,
		ServerHost:      "127.0.0.1",
		ServerPort:      8000,
		RecentDocuments: make([]RecentDocument, 0),
	}
}

func (s *AppState) IsOffline() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.OfflineMode || os.Getenv("SCANDOC_OFFLINE") == "1"
}

func (s *AppState) ToggleOfflineMode() bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.OfflineMode = !s.OfflineMode
	if s.OfflineMode {
		os.Setenv("SCANDOC_OFFLINE", "1")
	} else {
		os.Setenv("SCANDOC_OFFLINE", "0")
	}
	return s.OfflineMode
}

func (s *AppState) NavigateTo(screen string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.PreviousScreen = s.CurrentScreen
	s.CurrentScreen = screen
}

func (s *AppState) NavigateBack() {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.PreviousScreen != "" {
		s.CurrentScreen, s.PreviousScreen = s.PreviousScreen, ""
	} else {
		s.CurrentScreen = ScreenHome
	}
}

func (s *AppState) AddLog(msg string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.ProcessingLogs = append(s.ProcessingLogs, msg)
	if len(s.ProcessingLogs) > 500 {
		s.ProcessingLogs = s.ProcessingLogs[1:]
	}
}

func (s *AppState) AddRecent(path string, status string) {
	s.mu.Lock()
	defer s.mu.Unlock()

	fi, err := os.Stat(path)
	var size int64 = 0
	if err == nil {
		size = fi.Size()
	}

	cleanPath := filepath.Clean(path)
	name := filepath.Base(cleanPath)

	rec := RecentDocument{
		Name:      name,
		Path:      cleanPath,
		Status:    status,
		SizeBytes: size,
		Timestamp: time.Now(),
	}

	filtered := make([]RecentDocument, 0, len(s.RecentDocuments))
	for _, r := range s.RecentDocuments {
		if !strings.EqualFold(r.Path, cleanPath) {
			filtered = append(filtered, r)
		}
	}

	s.RecentDocuments = append([]RecentDocument{rec}, filtered...)
	if len(s.RecentDocuments) > 20 {
		s.RecentDocuments = s.RecentDocuments[:20]
	}
}
