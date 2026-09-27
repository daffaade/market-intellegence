package tests

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	deliveryhttp "be/internal/delivery/http"
	"be/internal/delivery/http/handler"
	"be/internal/domain"
	"be/internal/platform/config"
	"be/internal/platform/logger"
	"be/internal/repository/memory"
	"be/internal/usecase"
)

func setupTestRouter() http.Handler {
	cfg := &config.Config{
		Port:            "8080",
		LogLevel:        "debug",
		AIProvider:      "mock",
		AIModel:         "gemini-3.5-flash",
		PythonEngineURL: "http://localhost:8000",
		MockSectors:     true,
	}
	log := logger.InitLogger("debug")
	memRepo := memory.NewMemoryRepository()

	compUsecase := usecase.NewCompanyUsecase(memRepo)
	intelUsecase := usecase.NewIntelligenceUsecase(memRepo, memRepo, &mockIntelligenceEngineClient{}, &mockAIExplanationClient{}, cfg)
	scannerUsecase := usecase.NewScannerUsecase(intelUsecase, memRepo)
	analyticsUsecase := usecase.NewAnalyticsUsecase(memRepo)

	handlers := deliveryhttp.Handlers{
		Health:       handler.NewHealthHandler(cfg),
		Company:      handler.NewCompanyHandler(compUsecase),
		Intelligence: handler.NewIntelligenceHandler(intelUsecase),
		Scanner:      handler.NewScannerHandler(scannerUsecase),
		Analytics:    handler.NewAnalyticsHandler(analyticsUsecase),
	}

	return deliveryhttp.NewRouter(handlers, log)
}

func Test18EmitenCoverage(t *testing.T) {
	router := setupTestRouter()

	// 1. Check all companies count >= 18
	req := httptest.NewRequest(http.MethodGet, "/api/v1/companies", nil)
	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200 OK, got %d", rec.Code)
	}

	var compResp struct {
		Status string           `json:"status"`
		Data   []domain.Company `json:"data"`
	}
	if err := json.Unmarshal(rec.Body.Bytes(), &compResp); err != nil {
		t.Fatalf("failed to decode companies response: %v", err)
	}

	if len(compResp.Data) < 18 {
		t.Errorf("expected at least 18 companies, got %d", len(compResp.Data))
	}

	// 2. Check BBRI, BMRI, BBNI, ICBP, UNVR, ADRO, GOTO directly
	symbolsToCheck := []string{"BBRI", "BMRI", "BBNI", "ICBP", "UNVR", "ADRO", "GOTO"}
	for _, sym := range symbolsToCheck {
		r := httptest.NewRequest(http.MethodGet, "/api/v1/companies/"+sym, nil)
		w := httptest.NewRecorder()
		router.ServeHTTP(w, r)
		if w.Code != http.StatusOK {
			t.Errorf("expected 200 for %s, got %d", sym, w.Code)
		}

		// Also check intelligence
		rInt := httptest.NewRequest(http.MethodGet, "/api/v1/companies/"+sym+"/intelligence", nil)
		wInt := httptest.NewRecorder()
		router.ServeHTTP(wInt, rInt)
		if wInt.Code != http.StatusOK {
			t.Errorf("expected 200 for %s intelligence, got %d", sym, wInt.Code)
		}
	}
}

func TestAnalyticsEndpoints(t *testing.T) {
	router := setupTestRouter()

	// 1. Growth Timeline
	req := httptest.NewRequest(http.MethodGet, "/api/v1/market/growth-timeline", nil)
	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("growth timeline returned %d", rec.Code)
	}

	var timelineResp struct {
		Status string                             `json:"status"`
		Data   []domain.MarketGrowthTimelinePoint `json:"data"`
	}
	if err := json.Unmarshal(rec.Body.Bytes(), &timelineResp); err != nil {
		t.Fatalf("unmarshal error: %v", err)
	}
	if len(timelineResp.Data) < 12 {
		t.Errorf("expected at least 12 periods, got %d", len(timelineResp.Data))
	}

	// 2. Company Fundamentals (BBCA)
	reqFund := httptest.NewRequest(http.MethodGet, "/api/v1/companies/BBCA/fundamentals", nil)
	recFund := httptest.NewRecorder()
	router.ServeHTTP(recFund, reqFund)

	if recFund.Code != http.StatusOK {
		t.Fatalf("fundamentals returned %d", recFund.Code)
	}

	var fundResp struct {
		Status string                     `json:"status"`
		Data   domain.CompanyFundamentals `json:"data"`
	}
	if err := json.Unmarshal(recFund.Body.Bytes(), &fundResp); err != nil {
		t.Fatalf("unmarshal fundamentals error: %v", err)
	}
	if fundResp.Data.Symbol != "BBCA" {
		t.Errorf("expected BBCA fundamentals, got %s", fundResp.Data.Symbol)
	}
	if len(fundResp.Data.GrowthData) == 0 || len(fundResp.Data.Dividends) == 0 {
		t.Errorf("expected non-empty growth and dividend data")
	}

	// 3. Pipeline Telemetry
	reqTel := httptest.NewRequest(http.MethodGet, "/api/v1/pipeline/telemetry", nil)
	recTel := httptest.NewRecorder()
	router.ServeHTTP(recTel, reqTel)

	if recTel.Code != http.StatusOK {
		t.Fatalf("pipeline telemetry returned %d", recTel.Code)
	}

	var telResp struct {
		Status string                   `json:"status"`
		Data   domain.PipelineTelemetry `json:"data"`
	}
	if err := json.Unmarshal(recTel.Body.Bytes(), &telResp); err != nil {
		t.Fatalf("unmarshal telemetry error: %v", err)
	}
	if len(telResp.Data.Stages) != 6 {
		t.Errorf("expected 6 pipeline stages, got %d", len(telResp.Data.Stages))
	}

	// 4. Macro Indicators
	reqMacro := httptest.NewRequest(http.MethodGet, "/api/v1/macro/indicators", nil)
	recMacro := httptest.NewRecorder()
	router.ServeHTTP(recMacro, reqMacro)

	if recMacro.Code != http.StatusOK {
		t.Fatalf("macro indicators returned %d", recMacro.Code)
	}

	// 5. Disaster Risks
	reqDis := httptest.NewRequest(http.MethodGet, "/api/v1/macro/disaster-risks", nil)
	recDis := httptest.NewRecorder()
	router.ServeHTTP(recDis, reqDis)

	if recDis.Code != http.StatusOK {
		t.Fatalf("disaster risks returned %d", recDis.Code)
	}
}

func TestMemoryAnalyticsRepository_Direct(t *testing.T) {
	ctx := context.Background()
	repo := memory.NewMemoryRepository()

	// Verify fallback generation for symbol with no bespoke entry
	fund, err := repo.GetFundamentals(ctx, "ICBP")
	if err != nil {
		t.Fatalf("failed to get fundamentals for ICBP: %v", err)
	}
	if fund.Symbol != "ICBP" || len(fund.GrowthData) == 0 {
		t.Errorf("unexpected ICBP fallback fundamentals: %+v", fund)
	}

	// Verify invalid symbol
	_, err = repo.GetFundamentals(ctx, "NONEXISTENT")
	if err == nil {
		t.Errorf("expected error for non-existent company")
	}
}
