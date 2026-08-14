package backend

import (
	"context"

	"scandoc/internal/tui/state"
)

type DocumentInfo struct {
	Path      string `json:"path"`
	Name      string `json:"name"`
	PageCount int    `json:"page_count"`
	MimeType  string `json:"mime_type"`
}

type ModelInfo struct {
	ModelID   string `json:"model_id"`
	Name      string `json:"name"`
	Installed bool   `json:"installed"`
	SizeBytes int64  `json:"size_bytes"`
}

type DocumentService interface {
	Inspect(ctx context.Context, path string) (*DocumentInfo, error)
	Process(ctx context.Context, path string, config state.PipelineConfig) error
	Export(ctx context.Context, path string, format string, outputDir string) (string, error)
}

type ModelService interface {
	ListModels(ctx context.Context) ([]ModelInfo, error)
	DownloadModel(ctx context.Context, modelID string) error
	ClearCache(ctx context.Context, modelID string) error
}

type BenchmarkService interface {
	RunBenchmark(ctx context.Context) (map[string]any, error)
}

type ServerService interface {
	StartServer(ctx context.Context, host string, port int) error
	StopServer(ctx context.Context) error
	IsRunning() bool
}

type Services struct {
	Document DocumentService
	Model    ModelService
	Bench    BenchmarkService
	Server   ServerService
}
