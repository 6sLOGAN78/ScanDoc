package backend

import (
	"context"
	"fmt"
	"path/filepath"
	"time"

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
	return nil
}

func (s *MockDocumentService) Export(ctx context.Context, path string, format string, outputDir string) (string, error) {
	out := filepath.Join(outputDir, fmt.Sprintf("%s.%s", filepath.Base(path), format))
	return out, nil
}

type MockModelService struct {
	installed map[string]bool
}

func NewMockModelService() *MockModelService {
	return &MockModelService{
		installed: map[string]bool{
			"rapidocr_onnx":    true,
			"rtdetr_doclaynet": true,
			"slanet_table":     true,
			"pix2text_formula": false,
			"smolvlm_local":    false,
		},
	}
}

func (s *MockModelService) ListModels(ctx context.Context) ([]ModelInfo, error) {
	return []ModelInfo{
		{ModelID: "rapidocr_onnx", Name: "RapidOCR PP-OCRv4 ONNX", Installed: s.installed["rapidocr_onnx"], SizeBytes: 10857312},
		{ModelID: "rtdetr_doclaynet", Name: "RT-DETR DocLayNet Layout Analyzer", Installed: s.installed["rtdetr_doclaynet"], SizeBytes: 44281920},
		{ModelID: "slanet_table", Name: "SLANet Table Recognizer", Installed: s.installed["slanet_table"], SizeBytes: 18492000},
		{ModelID: "pix2text_formula", Name: "Pix2Text LaTeX-OCR Vision Model", Installed: s.installed["pix2text_formula"], SizeBytes: 18920112},
		{ModelID: "smolvlm_local", Name: "SmolVLM Multimodal Model", Installed: s.installed["smolvlm_local"], SizeBytes: 512000000},
	}, nil
}

func (s *MockModelService) DownloadModel(ctx context.Context, modelID string) error {
	time.Sleep(100 * time.Millisecond)
	s.installed[modelID] = true
	return nil
}

func (s *MockModelService) ClearCache(ctx context.Context, modelID string) error {
	s.installed[modelID] = false
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
