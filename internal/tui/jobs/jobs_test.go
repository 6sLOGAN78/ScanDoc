package jobs

import (
	"testing"
)

func TestJobManagerLifecycle(t *testing.T) {
	jm := NewJobManager()
	job := jm.CreateJob("/tmp/sample.pdf", "Pipeline Task")

	if job.Status != JobQueued {
		t.Errorf("Expected initial status %s, got %s", JobQueued, job.Status)
	}

	found := jm.GetJob(job.ID)
	if found == nil {
		t.Fatalf("Expected to find job %s, got nil", job.ID)
	}

	cancelled := jm.CancelJob(job.ID)
	if !cancelled {
		t.Errorf("Expected CancelJob to return true")
	}

	if found.Status != JobCancelled {
		t.Errorf("Expected status %s after cancel, got %s", JobCancelled, found.Status)
	}
}
