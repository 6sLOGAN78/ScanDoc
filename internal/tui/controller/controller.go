package controller

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"scandoc/internal/tui/backend"
	"scandoc/internal/tui/events"
	"scandoc/internal/tui/jobs"
	"scandoc/internal/tui/logger"
	"scandoc/internal/tui/state"
)

type FileItem struct {
	Path       string    `json:"path"`
	Name       string    `json:"name"`
	IsDir      bool      `json:"is_dir"`
	SizeBytes  int64     `json:"size_bytes"`
	FormatDesc string    `json:"format_desc"`
	ModTime    time.Time `json:"mod_time"`
}

type Controller struct {
	State    *state.AppState
	Services *backend.Services
	Jobs     *jobs.JobManager
	Events   *events.EventBus
}

func NewController(st *state.AppState, services *backend.Services) *Controller {
	if st == nil {
		st = state.NewAppState()
	}
	if services == nil {
		services = backend.NewMockServices()
	}
	return &Controller{
		State:    st,
		Services: services,
		Jobs:     jobs.DefaultJobManager,
		Events:   events.DefaultEventBus,
	}
}

func (c *Controller) ListDirectoryFiles(targetDir string) ([]FileItem, error) {
	if targetDir == "" {
		targetDir = c.State.CurrentDir
	}

	cleanDir := filepath.Clean(targetDir)
	entries, err := os.ReadDir(cleanDir)
	if err != nil {
		cleanDir, _ = os.Getwd()
		entries, _ = os.ReadDir(cleanDir)
	}

	c.State.CurrentDir = cleanDir
	items := make([]FileItem, 0, len(entries))

	for _, entry := range entries {
		name := entry.Name()
		if strings.HasPrefix(name, ".") {
			continue
		}

		if c.State.SearchQuery != "" && !strings.Contains(strings.ToLower(name), strings.ToLower(c.State.SearchQuery)) {
			continue
		}

		fullPath := filepath.Join(cleanDir, name)
		if entry.IsDir() {
			items = append(items, FileItem{
				Path:       fullPath,
				Name:       name,
				IsDir:      true,
				SizeBytes:  0,
				FormatDesc: "Folder",
			})
		} else {
			ext := filepath.Ext(name)
			if c.State.ExtensionFilter != "" && !strings.EqualFold(ext, c.State.ExtensionFilter) {
				continue
			}

			info, _ := entry.Info()
			var size int64 = 0
			if info != nil {
				size = info.Size()
			}

			desc := "FILE"
			if len(ext) > 1 {
				desc = strings.ToUpper(ext[1:])
			}

			items = append(items, FileItem{
				Path:       fullPath,
				Name:       name,
				IsDir:      false,
				SizeBytes:  size,
				FormatDesc: desc,
			})
		}
	}

	sort.Slice(items, func(i, j int) bool {
		if items[i].IsDir != items[j].IsDir {
			return items[i].IsDir
		}
		return strings.ToLower(items[i].Name) < strings.ToLower(items[j].Name)
	})

	return items, nil
}

func (c *Controller) ListWorkspaceFiles(dir string) ([]FileItem, error) {
	cleanDir := filepath.Clean(dir)
	entries, err := os.ReadDir(cleanDir)
	if err != nil {
		return nil, err
	}

	var items []FileItem
	for _, entry := range entries {
		if strings.HasPrefix(entry.Name(), ".") {
			continue
		}

		fullPath := filepath.Join(cleanDir, entry.Name())
		info, _ := entry.Info()
		var size int64 = 0
		var modTime time.Time
		if info != nil {
			size = info.Size()
			modTime = info.ModTime()
		}

		if entry.IsDir() {
			items = append(items, FileItem{
				Path:       fullPath,
				Name:       entry.Name(),
				IsDir:      true,
				SizeBytes:  size,
				ModTime:    modTime,
				FormatDesc: "Folder",
			})
		} else {
			ext := filepath.Ext(entry.Name())
			desc := "FILE"
			if len(ext) > 1 {
				desc = strings.ToUpper(ext[1:])
			}
			items = append(items, FileItem{
				Path:       fullPath,
				Name:       entry.Name(),
				IsDir:      false,
				SizeBytes:  size,
				ModTime:    modTime,
				FormatDesc: desc,
			})
		}
	}

	sort.Slice(items, func(i, j int) bool {
		if items[i].IsDir != items[j].IsDir {
			return items[i].IsDir
		}
		// Sort by modification time ascending (oldest first)
		return items[i].ModTime.Before(items[j].ModTime)
	})

	return items, nil
}

func (c *Controller) StartProcessing(ctx context.Context, paths []string) error {
	if len(paths) == 0 {
		c.State.AddLog("No documents selected to process.")
		logger.LogAction("PROCESS_START_FAILED", "No documents selected")
		return nil
	}

	logger.LogAction("PROCESS_START", fmt.Sprintf("Starting pipeline for %d documents", len(paths)))
	c.State.ProcessingStatus = "processing"
	c.State.ProgressStage = "Starting Pipeline"
	c.State.ProgressPct = 0.0

	for idx, path := range paths {
		job := c.Jobs.CreateJob(path, "Pipeline Task")
		job.Status = jobs.JobRunning
		job.CurrentStage = fmt.Sprintf("Processing (%d/%d): %s", idx+1, len(paths), filepath.Base(path))

		c.State.ProgressStage = job.CurrentStage
		c.State.ProgressPct = float64(idx) / float64(len(paths)) * 100.0

		err := c.Services.Document.Process(ctx, path, c.State.PipelineConfig)
		if err == nil {
			job.Status = jobs.JobCompleted
			c.State.ActiveDocumentPath = path
			c.State.ActiveDocumentName = filepath.Base(path)
			c.State.AddRecent(path, "completed")
			c.State.AddLog("Successfully processed: " + filepath.Base(path))
		} else {
			job.Status = jobs.JobFailed
			job.ErrorMessage = err.Error()
			c.State.ProcessingErrors = append(c.State.ProcessingErrors, path+": "+err.Error())
			c.State.AddLog("Processing failed: " + err.Error())
		}
	}

	c.State.ProgressPct = 100.0
	c.State.ProgressStage = "Completed"
	c.State.ProcessingStatus = "completed"

	return nil
}
