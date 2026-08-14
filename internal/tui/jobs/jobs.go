package jobs

import (
	"context"
	"path/filepath"
	"sort"
	"sync"
	"time"

	"scandoc/internal/tui/events"
)

type JobStatus string

const (
	JobQueued    JobStatus = "QUEUED"
	JobRunning   JobStatus = "RUNNING"
	JobCompleted JobStatus = "COMPLETED"
	JobFailed    JobStatus = "FAILED"
	JobCancelled JobStatus = "CANCELLED"
)

type Job struct {
	ID           string             `json:"id"`
	DocumentPath string             `json:"document_path"`
	TaskName     string             `json:"task_name"`
	Status       JobStatus          `json:"status"`
	ProgressPct  float64            `json:"progress_pct"`
	CurrentStage string             `json:"current_stage"`
	StartedAt    time.Time          `json:"started_at"`
	FinishedAt   time.Time          `json:"finished_at"`
	ErrorMessage string             `json:"error_message"`
	ResultData   any                `json:"result_data"`
	CancelFunc   context.CancelFunc `json:"-"`
}

type JobManager struct {
	mu   sync.RWMutex
	jobs map[string]*Job
}

func NewJobManager() *JobManager {
	return &JobManager{
		jobs: make(map[string]*Job),
	}
}

func (m *JobManager) CreateJob(docPath string, taskName string) *Job {
	m.mu.Lock()
	defer m.mu.Unlock()

	id := time.Now().Format("150405") + "_" + filepath.Base(docPath)
	if len(id) > 16 {
		id = id[:16]
	}

	job := &Job{
		ID:           id,
		DocumentPath: docPath,
		TaskName:     taskName,
		Status:       JobQueued,
		ProgressPct:  0.0,
		CurrentStage: "Pending",
		StartedAt:    time.Now(),
	}

	m.jobs[id] = job

	events.DefaultEventBus.Publish(events.AppEvent{
		Type:      events.EventJobStatusChanged,
		Timestamp: time.Now(),
		Payload: map[string]any{
			"job_id": id,
			"status": JobQueued,
		},
		Message: "Job queued: " + filepath.Base(docPath),
	})

	return job
}

func (m *JobManager) ListJobs() []*Job {
	m.mu.RLock()
	defer m.mu.RUnlock()

	res := make([]*Job, 0, len(m.jobs))
	for _, j := range m.jobs {
		res = append(res, j)
	}

	sort.Slice(res, func(i, j int) bool {
		return res[i].StartedAt.After(res[j].StartedAt)
	})

	return res
}

func (m *JobManager) GetJob(id string) *Job {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.jobs[id]
}

func (m *JobManager) CancelJob(id string) bool {
	m.mu.Lock()
	defer m.mu.Unlock()

	job, exists := m.jobs[id]
	if !exists {
		return false
	}

	if job.Status == JobQueued || job.Status == JobRunning {
		job.Status = JobCancelled
		job.FinishedAt = time.Now()
		if job.CancelFunc != nil {
			job.CancelFunc()
		}

		events.DefaultEventBus.Publish(events.AppEvent{
			Type:      events.EventJobStatusChanged,
			Timestamp: time.Now(),
			Payload: map[string]any{
				"job_id": id,
				"status": JobCancelled,
			},
			Message: "Job cancelled: " + id,
		})

		return true
	}

	return false
}

var DefaultJobManager = NewJobManager()
