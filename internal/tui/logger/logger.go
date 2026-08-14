package logger

import (
	"fmt"
	"io"
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

	// Also setup global log file
	home, _ := os.UserHomeDir()
	globalLogDir := filepath.Join(home, ".scandoc", "logs")
	os.MkdirAll(globalLogDir, 0755)
	globalPath := filepath.Join(globalLogDir, "events.log")
	globalLogFile, err := os.OpenFile(globalPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	
	var writers []io.Writer
	writers = append(writers, logFile)
	if err == nil {
		writers = append(writers, globalLogFile)
	}
	
	multiWriter := io.MultiWriter(writers...)
	logger = log.New(multiWriter, "", log.LstdFlags)
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
