package logger

import (
	"fmt"
	"log"
	"os"
	"path/filepath"
)

var (
	logFile *os.File
	logger  *log.Logger
)

func Init() error {
	logDir := "./local/scandoc/logs"
	if err := os.MkdirAll(logDir, 0755); err != nil {
		return err
	}

	path := filepath.Join(logDir, "events.log")
	var err error
	logFile, err = os.OpenFile(path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}

	logger = log.New(logFile, "", log.LstdFlags)
	return nil
}

func LogEvent(eventType, message string) {
	if logger != nil {
		logger.Printf("[%s] %s\n", eventType, message)
	}
}

func LogAction(action string, details string) {
	LogEvent("ACTION", fmt.Sprintf("%s - %s", action, details))
}

func LogKeyPress(key string, currentScreen string) {
	LogEvent("KEYPRESS", fmt.Sprintf("Key: '%s' | Screen: %s", key, currentScreen))
}

func Close() {
	if logFile != nil {
		logFile.Close()
	}
}
