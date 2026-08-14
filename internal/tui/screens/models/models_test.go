package models

import (
	"strings"
	"testing"

	"scandoc/internal/tui/backend"
	"scandoc/internal/tui/state"
)

func TestModelsRender(t *testing.T) {
	st := state.NewAppState()
	mockList := []backend.ModelInfo{
		{ModelID: "rapidocr_onnx", Name: "RapidOCR PP-OCRv4", Installed: true, SizeBytes: 10857312},
	}

	view := Render(st, mockList, 0)
	if !strings.Contains(view, "Model Lifecycle & Local Cache Manager") {
		t.Errorf("Expected title in view, got: %s", view)
	}

	if !strings.Contains(view, "rapidocr_onnx") {
		t.Errorf("Expected model ID rapidocr_onnx in view, got: %s", view)
	}
}
