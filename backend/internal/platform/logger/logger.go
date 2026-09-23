package logger

import (
	"log/slog"
	"os"
	"strings"
)

// InitLogger initializes and returns a structured JSON slog.Logger.
// It also sets the returned logger as the default slog logger.
func InitLogger(level string) *slog.Logger {
	var lvl slog.Level
	switch strings.ToLower(strings.TrimSpace(level)) {
	case "debug":
		lvl = slog.LevelDebug
	case "info":
		lvl = slog.LevelInfo
	case "warn", "warning":
		lvl = slog.LevelWarn
	case "error":
		lvl = slog.LevelError
	default:
		lvl = slog.LevelInfo
	}

	opts := &slog.HandlerOptions{
		Level: lvl,
	}

	handler := slog.NewJSONHandler(os.Stdout, opts)
	l := slog.New(handler)
	slog.SetDefault(l)

	return l
}
