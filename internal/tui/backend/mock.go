package backend

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"scandoc/internal/tui/logger"
	"scandoc/internal/tui/state"
)

type MockDocumentService struct{}

func (s *MockDocumentService) Inspect(ctx context.Context, path string) (*DocumentInfo, error) {
	return &DocumentInfo{
		Path:      path,
		Name:      filepath.Base(path),
		PageCount: 3,
		MimeType:  "application/pdf",
	}, nil
}

func (s *MockDocumentService) Process(ctx context.Context, path string, config state.PipelineConfig) error {
	time.Sleep(100 * time.Millisecond)

	outDir := filepath.Join("./local/scandoc/output", filepath.Base(path))
	os.MkdirAll(outDir, 0755)

	// Simulate copying the original file
	info, err := os.Stat(path)
	if err == nil && !info.IsDir() {
		inputData, _ := os.ReadFile(path)
		os.WriteFile(filepath.Join(outDir, filepath.Base(path)), inputData, 0644)
	} else if err == nil && info.IsDir() {
		// Just a dummy file to represent the scanned folder original
		os.WriteFile(filepath.Join(outDir, "scanned_folder_index.txt"), []byte("folder scanned: "+path), 0644)
	}

	// Output chunks
	chunksData := `{"chunks": [{"id": 1, "text": "Extracted text chunk 1"}, {"id": 2, "text": "Extracted text chunk 2"}]}`
	os.WriteFile(filepath.Join(outDir, "chunks.json"), []byte(chunksData), 0644)

	logger.LogAction("DOCUMENT_PROCESS", "Processed and exported to: "+outDir)
	return nil
}

func (s *MockDocumentService) Export(ctx context.Context, path string, format string, outputDir string) (string, error) {
	out := filepath.Join(outputDir, fmt.Sprintf("%s.%s", filepath.Base(path), format))
	return out, nil
}

type MockModelService struct {
	modelDir string
}

func NewMockModelService() *MockModelService {
	dir := "./local/scandoc/models"
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
	path := filepath.Join(s.modelDir, modelID+".bin")
	_, err := os.Stat(path)
	return err == nil
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
	return err
}

func (s *MockModelService) ClearCache(ctx context.Context, modelID string) error {
	path := filepath.Join(s.modelDir, modelID+".bin")
	err := os.Remove(path)
	if err == nil {
		logger.LogAction("MODEL_UNINSTALL", "Successfully uninstalled model: "+modelID)
	} else if os.IsNotExist(err) {
		logger.LogAction("MODEL_UNINSTALL", "Model already uninstalled: "+modelID)
		return nil
	} else {
		logger.LogAction("MODEL_UNINSTALL_ERROR", "Failed to uninstall model: "+modelID+" error: "+err.Error())
	}
	return err
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
