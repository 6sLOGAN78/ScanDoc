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
	time.Sleep(100 * time.Millisecond) // Simulate processing time

	outDir := filepath.Join("./local/scandoc/output", filepath.Base(path))
	os.MkdirAll(outDir, 0755)

	// Create an images folder inside the output
	imagesDir := filepath.Join(outDir, "images")
	os.MkdirAll(imagesDir, 0755)
	
	// Dummy image
	os.WriteFile(filepath.Join(imagesDir, "page1_extracted_img1.png"), []byte("dummy image data"), 0644)

	// Copy the original file or folder using shell command for simplicity
	cmd := exec.Command("cp", "-r", path, outDir+"/")
	cmd.Run()

	// Extract some actual text to make chunks look real if it's a file
	var extractedText string
	info, err := os.Stat(path)
	if err == nil && !info.IsDir() {
		data, err := os.ReadFile(path)
		if err == nil {
			extractedText = string(data)
			if len(extractedText) > 200 {
				extractedText = extractedText[:200] + "..."
			}
			extractedText = strings.ReplaceAll(extractedText, "\n", " ")
			extractedText = strings.ReplaceAll(extractedText, "\"", "\\\"")
		}
	}
	if extractedText == "" {
		extractedText = "Sample extracted document text segment."
	}

	// Output chunks
	chunksData := fmt.Sprintf(`{"chunks": [{"id": 1, "text": "%s", "has_image": true}, {"id": 2, "text": "Additional context chunk"}]}`, extractedText)
	os.WriteFile(filepath.Join(outDir, "chunks.json"), []byte(chunksData), 0644)

	// Generate process.log
	logContent := fmt.Sprintf("=== scanDOC Processing Log ===\n")
	logContent += fmt.Sprintf("Date: %s\n", time.Now().Format(time.RFC1123))
	logContent += fmt.Sprintf("Target: %s\n\n", path)
	
	logContent += "--- Models Used ---\n"
	if config.EnableOCR { logContent += "- OCR Model: rapidocr_onnx\n" }
	if config.EnableLayout { logContent += "- Layout Analyzer: rtdetr_doclaynet\n" }
	if config.EnableTable { logContent += "- Table Recognizer: slanet_table\n" }
	if config.EnableFormula { logContent += "- Formula Extractor: pix2text_formula\n" }
	if config.EnableVLM { logContent += "- VLM: smolvlm_local\n" }
	logContent += fmt.Sprintf("Routing Mode: %s\n\n", config.RoutingMode)

	logContent += "--- Execution Stats ---\n"
	logContent += "Total Chunks Found: 2\n"
	logContent += "Total Chunks Stored: 2\n"
	logContent += "Images Extracted: 1\n"
	elapsed := time.Since(startTime)
	logContent += fmt.Sprintf("Total Processing Time: %v\n", elapsed)
	if config.EnableOCR { logContent += "  > OCR Processing Time: 45ms\n" }
	if config.EnableLayout { logContent += "  > Layout Analysis Time: 32ms\n" }
	
	os.WriteFile(filepath.Join(outDir, "process.log"), []byte(logContent), 0644)

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
	return err
}

func (s *MockModelService) ClearCache(ctx context.Context, modelID string) error {
	path1 := filepath.Join(s.modelDir, modelID)
	path2 := filepath.Join(s.modelDir, modelID+".bin")
	path3 := filepath.Join(s.modelDir, modelID+".pt")
	
	_ = os.Remove(path1)
	_ = os.Remove(path2)
	_ = os.Remove(path3)

	logger.LogAction("MODEL_UNINSTALL", "Successfully uninstalled model: "+modelID)
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
