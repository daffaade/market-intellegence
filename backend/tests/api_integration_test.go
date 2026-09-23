package tests

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"be/internal/adapter/llm"
	"be/internal/adapter/python_engine"
	deliveryhttp "be/internal/delivery/http"
	"be/internal/delivery/http/handler"
	"be/internal/platform/config"
	"be/internal/platform/logger"
	"be/internal/repository/memory"
	"be/internal/usecase"
)

func setupTestServer(t *testing.T) http.Handler {
	cfg := &config.Config{
		Port:          "8080",
		LogLevel:      "error",
		AIProvider:    "mock",
		AIModel:       "gemini-3.5-flash",
		MockSectors:   true,
		CacheTTLHours: 24,
	}
	log := logger.InitLogger(cfg.LogLevel)

	memRepo := memory.NewMemoryRepository()
	pyClient := python_engine.NewClient("http://localhost:8000") // Will fall back deterministically
	aiClient := llm.NewClient(cfg)

	compUsecase := usecase.NewCompanyUsecase(memRepo)
	intelUsecase := usecase.NewIntelligenceUsecase(memRepo, memRepo, pyClient, aiClient, cfg)
	scannerUsecase := usecase.NewScannerUsecase(intelUsecase, memRepo)

	handlers := deliveryhttp.Handlers{
		Health:       handler.NewHealthHandler(cfg),
		Company:      handler.NewCompanyHandler(compUsecase),
		Intelligence: handler.NewIntelligenceHandler(intelUsecase),
		Scanner:      handler.NewScannerHandler(scannerUsecase),
	}

	return deliveryhttp.NewRouter(handlers, log)
}

func TestAPI_HealthCheck(t *testing.T) {
	router := setupTestServer(t)

	req := httptest.NewRequest(http.MethodGet, "/api/v1/health", nil)
	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected status 200, got %d", rec.Code)
	}

	var resp map[string]interface{}
	if err := json.Unmarshal(rec.Body.Bytes(), &resp); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if resp["status"] != "success" {
		t.Errorf("expected status success, got %v", resp["status"])
	}

	data, ok := resp["data"].(map[string]interface{})
	if !ok || data["status"] != "ok" {
		t.Errorf("expected health data status ok, got %v", data)
	}
}

func TestAPI_CompaniesListAndDetail(t *testing.T) {
	router := setupTestServer(t)

	// 1. List Companies
	req := httptest.NewRequest(http.MethodGet, "/api/v1/companies", nil)
	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200 for list companies, got %d", rec.Code)
	}

	// 2. Get Detail BBCA
	reqDetail := httptest.NewRequest(http.MethodGet, "/api/v1/companies/BBCA", nil)
	recDetail := httptest.NewRecorder()
	router.ServeHTTP(recDetail, reqDetail)

	if recDetail.Code != http.StatusOK {
		t.Fatalf("expected 200 for BBCA detail, got %d", recDetail.Code)
	}
}

func TestAPI_CompanyIntelligence_And_Disclaimer(t *testing.T) {
	router := setupTestServer(t)

	req := httptest.NewRequest(http.MethodGet, "/api/v1/companies/BBCA/intelligence", nil)
	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200 for intelligence, got %d: %s", rec.Code, rec.Body.String())
	}

	var resp struct {
		Status string `json:"status"`
		Data   struct {
			Symbol            string `json:"symbol"`
			OpportunityScore  float64 `json:"opportunity_score"`
			Disclaimer        string `json:"disclaimer"`
			AIResearchSummary string `json:"ai_research_summary"`
		} `json:"data"`
	}

	if err := json.Unmarshal(rec.Body.Bytes(), &resp); err != nil {
		t.Fatalf("unmarshal error: %v", err)
	}

	if resp.Data.Symbol != "BBCA" {
		t.Errorf("expected symbol BBCA, got %s", resp.Data.Symbol)
	}

	// Strict requirement: Hackathon compliance disclaimer must be present!
	if resp.Data.Disclaimer == "" {
		t.Errorf("expected disclaimer to be non-empty for compliance")
	}

	if resp.Data.AIResearchSummary == "" {
		t.Errorf("expected AIResearchSummary to be synthesized")
	}
}

func TestAPI_CompanyAnomalies(t *testing.T) {
	router := setupTestServer(t)

	req := httptest.NewRequest(http.MethodGet, "/api/v1/companies/GOTO/anomalies", nil)
	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200 for GOTO anomalies, got %d", rec.Code)
	}

	var resp struct {
		Status string `json:"status"`
		Data   struct {
			Symbol    string  `json:"symbol"`
			IsAnomaly bool    `json:"is_anomaly"`
			AnomalyScore float64 `json:"anomaly_score"`
		} `json:"data"`
	}

	if err := json.Unmarshal(rec.Body.Bytes(), &resp); err != nil {
		t.Fatalf("unmarshal error: %v", err)
	}

	if resp.Data.Symbol != "GOTO" {
		t.Errorf("expected symbol GOTO, got %s", resp.Data.Symbol)
	}
	if !resp.Data.IsAnomaly {
		t.Errorf("expected GOTO to be flagged as anomaly")
	}
}

func TestAPI_MarketOverview_And_Screener(t *testing.T) {
	router := setupTestServer(t)

	// 1. Overview
	reqOverview := httptest.NewRequest(http.MethodGet, "/api/v1/market/overview", nil)
	recOverview := httptest.NewRecorder()
	router.ServeHTTP(recOverview, reqOverview)

	if recOverview.Code != http.StatusOK {
		t.Fatalf("expected 200 for overview, got %d", recOverview.Code)
	}

	// 2. Screener Filter
	filterBody := []byte(`{"sector":"Financials","min_opportunity":70}`)
	reqScreen := httptest.NewRequest(http.MethodPost, "/api/v1/screener", bytes.NewBuffer(filterBody))
	reqScreen.Header.Set("Content-Type", "application/json")
	recScreen := httptest.NewRecorder()
	router.ServeHTTP(recScreen, reqScreen)

	if recScreen.Code != http.StatusOK {
		t.Fatalf("expected 200 for screener, got %d", recScreen.Code)
	}
}
