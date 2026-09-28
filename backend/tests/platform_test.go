package tests

import (
	"os"
	"testing"

	"be/internal/platform/config"
	"be/internal/platform/logger"
)

func TestPlatformConfig(t *testing.T) {
	// Set custom environment variables
	os.Setenv("PORT", "9090")
	os.Setenv("MOCK_SECTORS", "true")
	os.Setenv("AI_PROVIDER", "groq")
	os.Setenv("AI_MODEL", "llama-3.3-70b-versatile")
	os.Setenv("LOG_LEVEL", "debug")
	os.Setenv("CACHE_TTL_HOURS", "48")

	cfg, err := config.LoadConfig()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if cfg.Port != "9090" {
		t.Errorf("expected port 9090, got %s", cfg.Port)
	}
	if !cfg.MockSectors {
		t.Errorf("expected MockSectors to be true")
	}
	if cfg.AIProvider != "groq" {
		t.Errorf("expected AIProvider to be groq, got %s", cfg.AIProvider)
	}
	if cfg.AIModel != "llama-3.3-70b-versatile" {
		t.Errorf("expected AIModel to be llama-3.3-70b-versatile, got %s", cfg.AIModel)
	}
	if cfg.LogLevel != "debug" {
		t.Errorf("expected LogLevel to be debug, got %s", cfg.LogLevel)
	}
	if cfg.CacheTTLHours != 48 {
		t.Errorf("expected CacheTTLHours to be 48, got %d", cfg.CacheTTLHours)
	}
}

func TestPlatformConfig_Defaults(t *testing.T) {
	// Clear environment variables to test defaults
	os.Unsetenv("PORT")
	os.Unsetenv("DATABASE_URL")
	os.Unsetenv("PYTHON_ENGINE_URL")
	os.Unsetenv("SECTORS_BASE_URL")
	os.Unsetenv("MOCK_SECTORS")
	os.Unsetenv("AI_PROVIDER")
	os.Unsetenv("AI_MODEL")
	os.Unsetenv("LOG_LEVEL")
	os.Unsetenv("CACHE_TTL_HOURS")

	cfg, err := config.LoadConfig()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if cfg.Port != "8080" {
		t.Errorf("expected default port 8080, got %s", cfg.Port)
	}
	if cfg.LogLevel != "info" {
		t.Errorf("expected default LogLevel to be info, got %s", cfg.LogLevel)
	}
	if cfg.DatabaseURL != "postgres://postgres:postgres@localhost:5432/market_intel?sslmode=disable" {
		t.Errorf("unexpected default database url: %s", cfg.DatabaseURL)
	}
	if cfg.PythonEngineURL != "http://localhost:8000" {
		t.Errorf("unexpected default python engine url: %s", cfg.PythonEngineURL)
	}
	if cfg.SectorsBaseURL != "https://api.sectors.app/v1" {
		t.Errorf("unexpected default sectors url: %s", cfg.SectorsBaseURL)
	}
	if cfg.MockSectors != false {
		t.Errorf("expected default MockSectors to be false")
	}
	if cfg.AIProvider != "mock" {
		t.Errorf("expected default AIProvider to be mock, got %s", cfg.AIProvider)
	}
	if cfg.AIModel != "gemini-3.5-flash" {
		t.Errorf("expected default AIModel to be gemini-3.5-flash, got %s", cfg.AIModel)
	}
	if cfg.CacheTTLHours != 24 {
		t.Errorf("expected default CacheTTLHours to be 24, got %d", cfg.CacheTTLHours)
	}
}

func TestPlatformLogger(t *testing.T) {
	levels := []string{"debug", "info", "warn", "error", "unknown"}
	for _, lvl := range levels {
		log := logger.InitLogger(lvl)
		if log == nil {
			t.Fatalf("expected logger for level %s to be initialized, got nil", lvl)
		}
	}
}
