package tests

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"

	"be/internal/adapter/llm"
	"be/internal/adapter/python_engine"
	appHttp "be/internal/delivery/http"
	"be/internal/delivery/http/handler"
	"be/internal/domain"
	"be/internal/platform/config"
	"be/internal/platform/logger"
	"be/internal/repository/memory"
	"be/internal/usecase"
)

func setupTestApp() http.Handler {
	cfg := &config.Config{
		Port:          "8080",
		LogLevel:      "error",
		AIProvider:    "mock",
		AIModel:       "gemini-3.5-flash",
		MockSectors:   true,
		CacheTTLHours: 24,
	}
	log := logger.InitLogger(cfg.LogLevel)
	pyClient := python_engine.NewClient("http://127.0.0.1:59999") // offline fallback
	companyRepo := memory.NewMemoryRepository()
	aiClient := llm.NewClient(cfg)

	compUc := usecase.NewCompanyUsecase(companyRepo)
	intelUc := usecase.NewIntelligenceUsecase(companyRepo, companyRepo, pyClient, aiClient, cfg)
	scannerUc := usecase.NewScannerUsecase(intelUc, companyRepo)
	analyticsUc := usecase.NewAnalyticsUsecase(companyRepo, companyRepo, &mockFundamentalsClient{})
	sectorUc := usecase.NewSectorUsecase(pyClient)

	handlers := appHttp.Handlers{
		Health:       handler.NewHealthHandler(cfg),
		Company:      handler.NewCompanyHandler(compUc),
		Intelligence: handler.NewIntelligenceHandler(intelUc),
		Scanner:      handler.NewScannerHandler(scannerUc),
		Analytics:    handler.NewAnalyticsHandler(analyticsUc),
		Sector:       handler.NewSectorHandler(sectorUc),
	}

	return appHttp.NewRouter(handlers, log)
}

func TestSectorEndpoints(t *testing.T) {
	app := setupTestApp()

	// 1. List Sectors
	req := httptest.NewRequest(http.MethodGet, "/api/v1/sectors", nil)
	rec := httptest.NewRecorder()
	app.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rec.Code)
	}

	var listResp map[string]any
	if err := json.Unmarshal(rec.Body.Bytes(), &listResp); err != nil {
		t.Fatalf("invalid json: %v", err)
	}
	sectors, ok := listResp["sectors"].([]any)
	if !ok || len(sectors) == 0 {
		t.Fatalf("expected non-empty sectors array, got %v", listResp)
	}

	// 2. Get Single Sector
	req = httptest.NewRequest(http.MethodGet, "/api/v1/sectors/Financials", nil)
	rec = httptest.NewRecorder()
	app.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rec.Code)
	}

	var secResp map[string]any
	if err := json.Unmarshal(rec.Body.Bytes(), &secResp); err != nil {
		t.Fatalf("invalid json: %v", err)
	}
	if secResp["sector"] != "Financials" {
		t.Fatalf("expected Financials, got %v", secResp["sector"])
	}
}

func TestIntelligenceEndpoint_EnrichedWithSmartMoneyAndCatalysts(t *testing.T) {
	app := setupTestApp()

	req := httptest.NewRequest(http.MethodGet, "/api/v1/companies/BBCA/intelligence", nil)
	rec := httptest.NewRecorder()
	app.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rec.Code)
	}

	var resp map[string]any
	if err := json.Unmarshal(rec.Body.Bytes(), &resp); err != nil {
		t.Fatalf("invalid json: %v", err)
	}

	data := resp
	if d, ok := resp["data"].(map[string]any); ok {
		data = d
	}

	if data["smart_money"] == nil {
		t.Fatalf("expected smart_money in response, got nil")
	}
	if data["catalysts"] == nil {
		t.Fatalf("expected catalysts in response, got nil")
	}
}

type mockSectorUsecase struct {
	getErr  error
	listErr error
}

func (m *mockSectorUsecase) GetSectorIntelligence(ctx context.Context, sectorName string) (*domain.SectorIntelligence, error) {
	if m.getErr != nil {
		return nil, m.getErr
	}
	return &domain.SectorIntelligence{Sector: sectorName}, nil
}

func (m *mockSectorUsecase) ListSectors(ctx context.Context) ([]domain.SectorIntelligence, error) {
	if m.listErr != nil {
		return nil, m.listErr
	}
	return []domain.SectorIntelligence{{Sector: "Financials"}}, nil
}

func TestSectorEndpoints_Errors(t *testing.T) {
	// 1. Sector Not Found -> 404
	hNotFound := handler.NewSectorHandler(&mockSectorUsecase{getErr: domain.ErrSectorNotFound})
	mux := http.NewServeMux()
	mux.HandleFunc("GET /api/v1/sectors/{sector}", hNotFound.GetSector)

	req := httptest.NewRequest(http.MethodGet, "/api/v1/sectors/NonExistent", nil)
	rec := httptest.NewRecorder()
	mux.ServeHTTP(rec, req)
	if rec.Code != http.StatusNotFound {
		t.Fatalf("expected 404, got %d", rec.Code)
	}

	// 2. Sector Internal Error -> 500
	hInternalErr := handler.NewSectorHandler(&mockSectorUsecase{getErr: errors.New("database failure")})
	muxErr := http.NewServeMux()
	muxErr.HandleFunc("GET /api/v1/sectors/{sector}", hInternalErr.GetSector)

	req = httptest.NewRequest(http.MethodGet, "/api/v1/sectors/Financials", nil)
	rec = httptest.NewRecorder()
	muxErr.ServeHTTP(rec, req)
	if rec.Code != http.StatusInternalServerError {
		t.Fatalf("expected 500, got %d", rec.Code)
	}

	// 3. List Sectors Internal Error -> 500
	hListErr := handler.NewSectorHandler(&mockSectorUsecase{listErr: errors.New("engine unreachable")})
	muxListErr := http.NewServeMux()
	muxListErr.HandleFunc("GET /api/v1/sectors", hListErr.ListSectors)

	req = httptest.NewRequest(http.MethodGet, "/api/v1/sectors", nil)
	rec = httptest.NewRecorder()
	muxListErr.ServeHTTP(rec, req)
	if rec.Code != http.StatusInternalServerError {
		t.Fatalf("expected 500, got %d", rec.Code)
	}
}

