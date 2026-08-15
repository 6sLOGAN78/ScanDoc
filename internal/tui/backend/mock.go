package backend

import (
	"context"
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
		cmd := exec.Command("cp", "-r", filepath.Join(os.Getenv("HOME"), "local", "scandoc") + "/.", globalDir)
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

type MockModelService struct {
	modelDir string
}

func NewMockModelService() *MockModelService {
	dir := filepath.Join(os.Getenv("HOME"), "local", "scandoc", "models")
	_ = os.MkdirAll(dir, 0755)
	
	// Create dummy files for default installed models if they don't exist yet
	defaultModels := []string{"rapidocr_onnx", "rtdetr_doclaynet", "slanet_table"}
	for _, m := range defaultModels {
		path := filepath.Join(dir, m+".bin")
		if _, err := os.Stat(path); os.IsNotExist(err) {
			os.WriteFile(path, []byte("dummy"), 0644)
		}
	}
	
	return &MockModelService{
		modelDir: dir,
	}
}

func (s *MockModelService) isInstalled(modelID string) bool {
	path1 := filepath.Join(s.modelDir, modelID)
	path2 := filepath.Join(s.modelDir, modelID+".bin")
	path3 := filepath.Join(s.modelDir, modelID+".pt")
	
	if _, err := os.Stat(path1); err == nil { return true }
	if _, err := os.Stat(path2); err == nil { return true }
	if _, err := os.Stat(path3); err == nil { return true }
	
	return false
}

func (s *MockModelService) ListModels(ctx context.Context) ([]ModelInfo, error) {
	return []ModelInfo{
		{ModelID: "rapidocr_onnx", Name: "RapidOCR PP-OCRv4 ONNX", Installed: s.isInstalled("rapidocr_onnx"), SizeBytes: 10857312},
		{ModelID: "rtdetr_doclaynet", Name: "RT-DETR DocLayNet Layout Analyzer", Installed: s.isInstalled("rtdetr_doclaynet"), SizeBytes: 44281920},
		{ModelID: "slanet_table", Name: "SLANet Table Recognizer", Installed: s.isInstalled("slanet_table"), SizeBytes: 18492000},
		{ModelID: "pix2text_formula", Name: "Pix2Text LaTeX-OCR Vision Model", Installed: s.isInstalled("pix2text_formula"), SizeBytes: 18920112},
		{ModelID: "smolvlm_local", Name: "SmolVLM Multimodal Model", Installed: s.isInstalled("smolvlm_local"), SizeBytes: 512000000},
	}, nil
}

func (s *MockModelService) DownloadModel(ctx context.Context, modelID string) error {
	time.Sleep(100 * time.Millisecond)
	path := filepath.Join(s.modelDir, modelID+".bin")
	err := os.WriteFile(path, []byte("dummy data"), 0644)
	if err == nil {
		logger.LogAction("MODEL_DOWNLOAD", "Successfully downloaded model: "+modelID)
	} else {
		logger.LogAction("MODEL_DOWNLOAD_ERROR", "Failed to download model: "+modelID+" error: "+err.Error())
	}
	syncToGlobal()
	return err
}

func (s *MockModelService) ClearCache(ctx context.Context, modelID string) error {
	path1 := filepath.Join(s.modelDir, modelID)
	path2 := filepath.Join(s.modelDir, modelID+".bin")
	path3 := filepath.Join(s.modelDir, modelID+".pt")

	removedAny := false
	if err := os.RemoveAll(path1); err == nil {
		removedAny = true
	}
	if err := os.RemoveAll(path2); err == nil {
		removedAny = true
	}
	if err := os.RemoveAll(path3); err == nil {
		removedAny = true
	}

	if !removedAny {
		logger.LogAction("MODEL_UNINSTALL_ERROR", "Failed to uninstall model or model not found: "+modelID)
		return fmt.Errorf("model not found")
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
