package config

import (
	"os"
	"strconv"

	"github.com/joho/godotenv"
)

type Config struct {
	Port            string
	DatabaseURL     string
	PythonEngineURL string
	SectorsAPIKey   string
	SectorsBaseURL  string
	MockSectors     bool
	AIProvider      string // "gemini", "groq", "mock"
	AIModel         string // "gemini-3.5-flash", "llama-3.3-70b-versatile"
	AIApiKey        string
	CacheTTLHours   int
}

func LoadConfig() (*Config, error) {
	_ = godotenv.Load()

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		dbURL = "postgres://postgres:postgres@localhost:5432/market_intel?sslmode=disable"
	}
	pyURL := os.Getenv("PYTHON_ENGINE_URL")
	if pyURL == "" {
		pyURL = "http://localhost:8000"
	}
	sectorsURL := os.Getenv("SECTORS_BASE_URL")
	if sectorsURL == "" {
		sectorsURL = "https://api.sectors.app/v1"
	}
	mockSectors, _ := strconv.ParseBool(os.Getenv("MOCK_SECTORS"))
	aiProvider := os.Getenv("AI_PROVIDER")
	if aiProvider == "" {
		aiProvider = "mock"
	}
	aiModel := os.Getenv("AI_MODEL")
	if aiModel == "" {
		aiModel = "gemini-3.5-flash"
	}
	cacheTTL, _ := strconv.Atoi(os.Getenv("CACHE_TTL_HOURS"))
	if cacheTTL <= 0 {
		cacheTTL = 24
	}

	return &Config{
		Port:            port,
		DatabaseURL:     dbURL,
		PythonEngineURL: pyURL,
		SectorsAPIKey:   os.Getenv("SECTORS_API_KEY"),
		SectorsBaseURL:  sectorsURL,
		MockSectors:     mockSectors,
		AIProvider:      aiProvider,
		AIModel:         aiModel,
		AIApiKey:        os.Getenv("AI_API_KEY"),
		CacheTTLHours:   cacheTTL,
	}, nil
}
