package backend

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"scandoc/internal/tui/logger"
	"scandoc/internal/tui/state"
)

type MockDocumentService struct{}

func syncToGlobal() {
	home, err := os.UserHomeDir()
	if err == nil {
		globalDir := filepath.Join(home, ".scandoc")
		os.MkdirAll(globalDir, 0755)
		cmd := exec.Command("cp", "-r", filepath.Join(os.Getenv("HOME"), "local", "scandoc")+"/.", globalDir)
		cmd.Run()
	}
}

func (s *MockDocumentService) Inspect(ctx context.Context, path string) (*DocumentInfo, error) {
	return &DocumentInfo{
		Path:      path,
		Name:      filepath.Base(path),
		PageCount: 3,
		MimeType:  "application/pdf",
	}, nil
}

func (s *MockDocumentService) Process(ctx context.Context, path string, config state.PipelineConfig) error {
	startTime := time.Now()

	outDir := filepath.Join(filepath.Join(os.Getenv("HOME"), "local", "scandoc", "output"), filepath.Base(path))
	os.MkdirAll(outDir, 0755)

	// Build the command
	// We'll use the python module directly assuming it's available in the environment
	args := []string{"-m", "scandoc.cli.main", "convert", path, "--output-dir", outDir, "-f", "json"}

	if config.RoutingMode != "" {
		args = append(args, "--routing-mode", config.RoutingMode)
	}
	if config.RoutingMode == "adaptive" || config.RoutingMode == "deep" {
		if config.OCRModel != "" {
			args = append(args, "--ocr-model", config.OCRModel)
		}
		if config.LayoutModel != "" {
			args = append(args, "--layout-model", config.LayoutModel)
		}
		if config.TableModel != "" {
			args = append(args, "--table-model", config.TableModel)
		}
		if config.FormulaModel != "" {
			args = append(args, "--formula-model", config.FormulaModel)
		}
	}

	cmd := exec.CommandContext(ctx, "python3", args...)

	// If src exists in current directory, add it to PYTHONPATH
	// This helps when running from the repo root.
	if _, err := os.Stat("src"); err == nil {
		cmd.Env = append(os.Environ(), "PYTHONPATH=src")
	} else {
		cmd.Env = os.Environ()
	}

	output, err := cmd.CombinedOutput()

	// Create images dir just in case
	imagesDir := filepath.Join(outDir, "images")
	os.MkdirAll(imagesDir, 0755)

	// Write log content
	logContent := fmt.Sprintf("=== scanDOC Processing Log ===\n")
	logContent += fmt.Sprintf("Date: %s\n", time.Now().Format(time.RFC1123))
	logContent += fmt.Sprintf("Target: %s\n\n", path)
	logContent += fmt.Sprintf("Command: python3 %s\n\n", strings.Join(args, " "))
	logContent += "--- CLI Output ---\n"
	logContent += string(output) + "\n\n"

	if err != nil {
		logContent += fmt.Sprintf("Error: %v\n", err)
	} else {
		logContent += "--- Execution Stats ---\n"
		elapsed := time.Since(startTime)
		logContent += fmt.Sprintf("Total Processing Time: %v\n", elapsed)
	}

	os.WriteFile(filepath.Join(outDir, "process.log"), []byte(logContent), 0644)

	if err != nil {
		logger.LogAction("DOCUMENT_PROCESS_ERROR", fmt.Sprintf("Failed processing %s: %v", path, err))
		syncToGlobal()
		return fmt.Errorf("conversion failed: %v", err)
	}

	logger.LogAction("DOCUMENT_PROCESS", "Processed and exported to: "+outDir)
	syncToGlobal()
	return nil
}

func (s *MockDocumentService) Export(ctx context.Context, path string, format string, outputDir string) (string, error) {
	out := filepath.Join(outputDir, fmt.Sprintf("%s.%s", filepath.Base(path), format))
	os.MkdirAll(outputDir, 0755)

	args := []string{"-m", "scandoc.cli.main", "convert", path, "--output-dir", outputDir, "-f", format}

	cmd := exec.CommandContext(ctx, "python3", args...)
	if _, err := os.Stat("src"); err == nil {
		cmd.Env = append(os.Environ(), "PYTHONPATH=src")
	} else {
		cmd.Env = os.Environ()
	}

	output, err := cmd.CombinedOutput()
	if err != nil {
		logger.LogAction("DOCUMENT_EXPORT_ERROR", fmt.Sprintf("Failed exporting %s to %s: %v\nOutput: %s", path, format, err, string(output)))
		return out, fmt.Errorf("export failed: %v", err)
	}

	logger.LogAction("DOCUMENT_EXPORT", fmt.Sprintf("Exported %s to %s format at %s", path, format, out))
	syncToGlobal()
	return out, nil
}

type MockModelService struct{}

func NewMockModelService() *MockModelService {
	return &MockModelService{}
}

func (s *MockModelService) ListModels(ctx context.Context) ([]ModelInfo, error) {
	cmd := exec.CommandContext(ctx, "python3", "-m", "scandoc.cli.main", "models", "status", "--json")
	if _, err := os.Stat("src"); err == nil {
		cmd.Env = append(os.Environ(), "PYTHONPATH=src")
	} else {
		cmd.Env = os.Environ()
	}

	output, err := cmd.CombinedOutput()
	if err != nil {
		return nil, fmt.Errorf("failed to list models from CLI: %v\nOutput: %s", err, string(output))
	}

	type CLIModelStatus struct {
		ModelID   string  `json:"model_id"`
		Name      string  `json:"name"`
		Task      string  `json:"task"`
		Installed bool    `json:"installed"`
		SizeMB    float64 `json:"size_mb"`
	}

	var statuses []CLIModelStatus

	// Skip potential warnings printed before JSON output
	outputStr := string(output)
	jsonStartIdx := strings.Index(outputStr, "[")
	if jsonStartIdx != -1 {
		outputStr = outputStr[jsonStartIdx:]
	}

	if err := json.Unmarshal([]byte(outputStr), &statuses); err != nil {
		return nil, fmt.Errorf("failed to parse models output: %v", err)
	}

	var results []ModelInfo
	for _, st := range statuses {
		results = append(results, ModelInfo{
			ModelID:   st.ModelID,
			Name:      st.Name,
			Installed: st.Installed,
			SizeBytes: int64(st.SizeMB * 1024 * 1024),
		})
	}
	return results, nil
}

func (s *MockModelService) DownloadModel(ctx context.Context, modelID string) error {
	cmd := exec.CommandContext(ctx, "python3", "-m", "scandoc.cli.main", "models", "download", modelID, "--json")
	if _, err := os.Stat("src"); err == nil {
		cmd.Env = append(os.Environ(), "PYTHONPATH=src")
	} else {
		cmd.Env = os.Environ()
	}

	output, err := cmd.CombinedOutput()
	if err != nil {
		logger.LogAction("MODEL_DOWNLOAD_ERROR", "Failed to download model: "+modelID+" error: "+err.Error())
		return fmt.Errorf("download failed: %v\nOutput: %s", err, string(output))
	}

	logger.LogAction("MODEL_DOWNLOAD", "Successfully downloaded model: "+modelID)
	syncToGlobal()
	return nil
}

func (s *MockModelService) ClearCache(ctx context.Context, modelID string) error {
	cmd := exec.CommandContext(ctx, "python3", "-m", "scandoc.cli.main", "models", "clear", modelID, "--json")
	if _, err := os.Stat("src"); err == nil {
		cmd.Env = append(os.Environ(), "PYTHONPATH=src")
	} else {
		cmd.Env = os.Environ()
	}

	output, err := cmd.CombinedOutput()
	if err != nil {
		logger.LogAction("MODEL_UNINSTALL_ERROR", "Failed to uninstall model: "+modelID+" error: "+err.Error())
		return fmt.Errorf("clear failed: %v\nOutput: %s", err, string(output))
	}

	logger.LogAction("MODEL_UNINSTALL", "Successfully uninstalled model: "+modelID)
	syncToGlobal()
	return nil
}

type MockBenchmarkService struct{}

func (s *MockBenchmarkService) RunBenchmark(ctx context.Context) (map[string]any, error) {
	return map[string]any{
		"scandoc_fps": 45.2,
		"docling_fps": 12.4,
		"speedup":     3.64,
	}, nil
}

type MockServerService struct {
	running bool
}

func (s *MockServerService) StartServer(ctx context.Context, host string, port int) error {
	s.running = true
	return nil
}

func (s *MockServerService) StopServer(ctx context.Context) error {
	s.running = false
	return nil
}

func (s *MockServerService) IsRunning() bool {
	return s.running
}

func NewMockServices() *Services {
	return &Services{
		Document: &MockDocumentService{},
		Model:    NewMockModelService(),
		Bench:    &MockBenchmarkService{},
		Server:   &MockServerService{},
	}
}
