# AI Engine P0/P1 Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the newly released AI Engine models (Smart Money, Catalyst Detector, and Sector Intelligence) into the Go Clean Architecture backend, exposing enriched company intelligence and dedicated sector intelligence REST endpoints.

**Architecture:** Extend the Go Clean Architecture (`domain` -> `adapter/python_engine` -> `usecase` -> `delivery/http`) with strict inwards dependency inversion. Enhance `domain.IntelligenceSnapshot` with `SmartMoney` and `Catalysts` models, create `domain.SectorIntelligence`, update `python_engine.Client` with new FastAPI router calls and deterministic fallbacks, and expose HTTP endpoints (`GET /api/v1/sectors`, `GET /api/v1/sectors/{sector}`, and enriched `GET /api/v1/companies/{symbol}/intelligence`).

**Tech Stack:** Go 1.22+, `net/http` standard mux, `slog` structured logging, `pgx/v5`, FastAPI (Python 3.10+ / `ai_engine`), JSON REST API.

## Global Constraints

- Domain purity: `internal/domain` must have zero third-party framework dependencies.
- Resilience: All external `ai_engine` HTTP calls must implement 8s timeout and fallback to deterministic local Prototype 3 heuristics when Python service is offline or cold-starting.
- Standard Library: Routing uses Go 1.22 `http.ServeMux` pattern (`METHOD /path/{param}`).
- 18 Emiten Coverage: All fallbacks and responses must gracefully support the 18 primary IDX tickers (`BBCA`, `BBRI`, `BMRI`, `BBNI`, `TLKM`, `ASII`, `AMRT`, `ICBP`, `INDF`, `UNVR`, `KLBF`, `GOTO`, `BUKA`, `ADRO`, `PTBA`, `ANTM`, `INCO`, `MDKA`).

---

### Task 1: Domain Entities for Smart Money, Catalysts, and Sector Intelligence

**Files:**
- Modify: `backend/internal/domain/intelligence.go:1-60`
- Create: `backend/internal/domain/sector.go`
- Test: `backend/tests/domain_test.go`

**Interfaces:**
- Produces:
  - `domain.SmartMoneySnapshot` struct
  - `domain.CatalystSnapshot` and `domain.CatalystEvent` structs
  - `domain.SectorIntelligence` and `domain.SectorMetrics` structs
  - `domain.SectorRepository` interface: `GetSector(ctx context.Context, name string) (*SectorIntelligence, error)` and `ListSectors(ctx context.Context) ([]SectorIntelligence, error)`

- [ ] **Step 1: Write unit test for domain structs and interfaces**

Create `backend/tests/domain_test.go`:
```go
package tests

import (
	"testing"
	"time"

	"be/internal/domain"
)

func TestDomainEntitiesInitialization(t *testing.T) {
	snap := domain.IntelligenceSnapshot{
		Symbol:           "BBCA",
		OpportunityScore: 78.5,
		RiskScore:        22.1,
		RiskLevel:        "Low",
		Direction:        "Bullish",
		Confidence:       "High",
		SmartMoney: &domain.SmartMoneySnapshot{
			State: "Accumulation",
			Score: 0.65,
			Components: map[string]float64{
				"cmf":                   0.4,
				"obv_trend":             0.7,
				"price_flow_divergence": 0.8,
			},
			Confidence: "medium",
			Evidence:   []string{"Hidden accumulation (harga turun, OBV naik)"},
		},
		Catalysts: &domain.CatalystSnapshot{
			CatalystScore: 0.8,
			NetDirection:  "Positive",
			Events: []domain.CatalystEvent{
				{
					Date:       "2026-09-28",
					Type:       "volume_shock",
					Layer:      "market",
					Direction:  "Positive",
					Strength:   0.85,
					Confidence: "high",
					Evidence:   []string{"Volume melonjak 2.3x dari median 20 hari"},
				},
			},
		},
		CreatedAt: time.Now(),
	}

	if snap.SmartMoney.State != "Accumulation" {
		t.Fatalf("expected SmartMoney state Accumulation, got %s", snap.SmartMoney.State)
	}
	if snap.Catalysts.CatalystScore != 0.8 {
		t.Fatalf("expected CatalystScore 0.8, got %f", snap.Catalysts.CatalystScore)
	}

	sec := domain.SectorIntelligence{
		Sector:         "Financials",
		AsOf:           "2026-09-28",
		NConstituents:  4,
		MomentumScore:  0.45,
		SentimentLabel: "Bullish",
		Metrics: domain.SectorMetrics{
			RsVsIhsg20d:  0.035,
			BreadthMa50:  0.75,
			AvgRisk:      "Low",
		},
		Evidence: []string{"3 dari 4 saham di atas MA50"},
	}

	if sec.SentimentLabel != "Bullish" {
		t.Fatalf("expected Bullish sentiment, got %s", sec.SentimentLabel)
	}
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `go test ./tests -run TestDomainEntitiesInitialization`
Expected: FAIL due to missing fields `SmartMoney`, `Catalysts`, and undefined types in `domain`.

- [ ] **Step 3: Update `domain/intelligence.go` and create `domain/sector.go`**

Update `backend/internal/domain/intelligence.go`:
```go
package domain

import (
	"context"
	"time"
)

type SmartMoneySnapshot struct {
	State      string             `json:"state"`
	Score      float64            `json:"score"`
	Components map[string]float64 `json:"components"`
	Confidence string             `json:"confidence"`
	Evidence   []string           `json:"evidence"`
}

type CatalystEvent struct {
	Date       string   `json:"date"`
	Type       string   `json:"type"`
	Layer      string   `json:"layer"`
	Direction  string   `json:"direction"`
	Strength   float64  `json:"strength"`
	Confidence string   `json:"confidence"`
	Evidence   []string `json:"evidence"`
}

type CatalystSnapshot struct {
	CatalystScore float64         `json:"catalyst_score"`
	NetDirection  string          `json:"net_direction"`
	Events        []CatalystEvent `json:"events"`
}

type IntelligenceSnapshot struct {
	Symbol                string                 `json:"symbol"`
	OpportunityScore      float64                `json:"opportunity_score"`
	RiskScore             float64                `json:"risk_score"`
	RiskLevel             string                 `json:"risk_level"`
	Direction             string                 `json:"direction"`
	Confidence            string                 `json:"confidence"`
	PositiveFactors       []string               `json:"positive_factors"`
	NegativeFactors       []string               `json:"negative_factors"`
	FundamentalDivergence *FundamentalDivergence `json:"fundamental_divergence,omitempty"`
	IsAnomaly             bool                   `json:"is_anomaly"`
	AnomalyReason         string                 `json:"anomaly_reason,omitempty"`
	SmartMoney            *SmartMoneySnapshot    `json:"smart_money,omitempty"`
	Catalysts             *CatalystSnapshot      `json:"catalysts,omitempty"`
	CreatedAt             time.Time              `json:"created_at"`
}

type IntelligenceRepository interface {
	GetLatestSnapshot(ctx context.Context, symbol string) (*IntelligenceSnapshot, error)
	ListSnapshots(ctx context.Context, symbol string, limit int) ([]IntelligenceSnapshot, error)
	SaveSnapshot(ctx context.Context, snapshot *IntelligenceSnapshot) error
}
```

Create `backend/internal/domain/sector.go`:
```go
package domain

import (
	"context"
	"errors"
)

var (
	ErrSectorNotFound = errors.New("sector not found")
	ErrInvalidSector  = errors.New("invalid sector name")
)

type SectorMetrics struct {
	RsVsIhsg20d        float64 `json:"rs_vs_ihsg_20d"`
	BreadthMa50        float64 `json:"breadth_ma50"`
	AvgOpportunity     float64 `json:"avg_opportunity"`
	AvgRisk            string  `json:"avg_risk"`
	DivergenceCount    int     `json:"divergence_count"`
	MedianPePercentile float64 `json:"median_pe_percentile"`
}

type SectorIntelligence struct {
	Sector          string        `json:"sector"`
	AsOf            string        `json:"as_of"`
	NConstituents   int           `json:"n_constituents"`
	LowConfidence   bool          `json:"low_confidence"`
	MomentumScore   float64       `json:"momentum_score"`
	SentimentLabel  string        `json:"sentiment_label"`
	RotationRank    int           `json:"rotation_rank"`
	RotationSignal  string        `json:"rotation_signal"`
	Metrics         SectorMetrics `json:"metrics"`
	Evidence        []string      `json:"evidence"`
	TopContributors []string      `json:"top_contributors"`
}

type SectorRepository interface {
	GetSector(ctx context.Context, sectorName string) (*SectorIntelligence, error)
	ListSectors(ctx context.Context) ([]SectorIntelligence, error)
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `go test ./tests -run TestDomainEntitiesInitialization -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add internal/domain/intelligence.go internal/domain/sector.go tests/domain_test.go
git commit -m "feat(domain): define SmartMoney, Catalyst, and SectorIntelligence entities"
```

---

### Task 2: Update Python Engine Adapter with Smart Money, Catalyst, and Sector API

**Files:**
- Modify: `backend/internal/adapter/python_engine/client.go:30-360`
- Test: `backend/tests/python_engine_test.go`

**Interfaces:**
- Consumes:
  - `domain.AnalyzeRequest`
  - `domain.IntelligenceSnapshot`
  - `domain.SectorIntelligence`
- Produces:
  - `client.Analyze(ctx, req)` returning enriched `IntelligenceSnapshot` (with `SmartMoney` & `Catalysts`)
  - `client.GetSectorIntelligence(ctx, sectorName)` returning `*domain.SectorIntelligence`
  - `client.ListSectorIntelligences(ctx)` returning `[]domain.SectorIntelligence`

- [ ] **Step 1: Write unit test for python_engine client with enriched mock server**

Create `backend/tests/python_engine_test.go`:
```go
package tests

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"be/internal/adapter/python_engine"
	"be/internal/domain"
)

func TestPythonEngineClient_AnalyzeWithNewModels(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/api/v1/analyze" {
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(map[string]any{
				"symbol": "BBCA",
				"opportunity_signal": map[string]any{
					"score":      72.4,
					"direction":  "Bullish",
					"confidence": "High",
					"positive_factors": []string{"Growth kuat"},
				},
				"risk_signal": map[string]any{
					"score": 18.0,
					"level": "Low",
				},
				"smart_money": map[string]any{
					"state": "Accumulation",
					"score": 0.45,
					"components": map[string]float64{
						"cmf": 0.35,
					},
					"confidence": "medium",
					"evidence": []string{"Akumulasi terdeteksi"},
				},
				"catalysts": map[string]any{
					"catalyst_score": 0.75,
					"net_direction": "Positive",
					"events": []map[string]any{
						{
							"type":      "volume_shock",
							"direction": "Positive",
							"strength":  0.8,
							"evidence":  []string{"Volume spike"},
						},
					},
				},
			})
			return
		}
		if r.URL.Path == "/api/v1/sector/Financials" {
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(map[string]any{
				"sector":          "Financials",
				"as_of":           "2026-09-28",
				"n_constituents":  4,
				"momentum_score":  0.32,
				"sentiment_label": "Bullish",
				"metrics": map[string]any{
					"rs_vs_ihsg_20d": 0.024,
					"breadth_ma50": 0.75,
				},
				"evidence": []string{"3 dari 4 saham uptrend"},
			})
			return
		}
		http.NotFound(w, r)
	}))
	defer ts.Close()

	client := python_engine.NewClient(ts.URL)
	snap, err := client.Analyze(context.Background(), domain.AnalyzeRequest{Symbol: "BBCA"})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if snap.SmartMoney == nil || snap.SmartMoney.State != "Accumulation" {
		t.Fatalf("expected smart money Accumulation, got %+v", snap.SmartMoney)
	}
	if snap.Catalysts == nil || snap.Catalysts.CatalystScore != 0.75 {
		t.Fatalf("expected catalyst score 0.75, got %+v", snap.Catalysts)
	}

	sec, err := client.GetSectorIntelligence(context.Background(), "Financials")
	if err != nil {
		t.Fatalf("failed to get sector intelligence: %v", err)
	}
	if sec.SentimentLabel != "Bullish" {
		t.Fatalf("expected Bullish, got %s", sec.SentimentLabel)
	}
}

func TestPythonEngineClient_FallbackWhenOffline(t *testing.T) {
	// Point to unreachable port
	client := python_engine.NewClient("http://127.0.0.1:59999")
	snap, err := client.Analyze(context.Background(), domain.AnalyzeRequest{Symbol: "BBCA"})
	if err != nil {
		t.Fatalf("expected fallback snapshot, got error: %v", err)
	}
	if snap.SmartMoney == nil {
		t.Fatalf("expected non-nil fallback SmartMoney")
	}
	if snap.Catalysts == nil {
		t.Fatalf("expected non-nil fallback Catalysts")
	}

	sec, err := client.GetSectorIntelligence(context.Background(), "Financials")
	if err != nil {
		t.Fatalf("expected fallback sector, got error: %v", err)
	}
	if sec.Sector != "Financials" {
		t.Fatalf("expected Financials, got %s", sec.Sector)
	}
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `go test ./tests -run TestPythonEngineClient -v`
Expected: FAIL due to missing methods `GetSectorIntelligence` and missing response parsing.

- [ ] **Step 3: Update `backend/internal/adapter/python_engine/client.go`**

Update `backend/internal/adapter/python_engine/client.go` to include:
- `IncludeSmartMoney: true` and `IncludeCatalysts: true` in request.
- Parse `pythonSmartMoneyOutput` and `pythonCatalystOutput`.
- Map them into `domain.IntelligenceSnapshot`.
- Provide fallback heuristics for Smart Money and Catalysts in `fallbackDeterministicSnapshot`.
- Add `GetSectorIntelligence(ctx, sectorName)` with fallback `fallbackSectorIntelligence(sectorName)`.
- Add `ListSectorIntelligences(ctx)` for all default sectors (`Financials`, `Energy`, `Basic Materials`, `Consumer Non-Cyclical`, `Technology`, `Infrastructure`, `Healthcare`, `Industrials`).

- [ ] **Step 4: Run test to verify it passes**

Run: `go test ./tests -run TestPythonEngineClient -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add internal/adapter/python_engine/client.go tests/python_engine_test.go
git commit -m "feat(adapter): add smart money, catalyst, and sector intelligence client methods"
```

---

### Task 3: Sector Intelligence Usecase & Repository Implementation

**Files:**
- Create: `backend/internal/usecase/sector_usecase.go`
- Modify: `backend/internal/repository/memory/memory_repo.go`
- Test: `backend/tests/sector_usecase_test.go`

**Interfaces:**
- Consumes:
  - `domain.SectorRepository` / `python_engine.Client`
- Produces:
  - `usecase.SectorUsecase` interface:
    - `GetSectorIntelligence(ctx context.Context, sectorName string) (*domain.SectorIntelligence, error)`
    - `ListSectors(ctx context.Context) ([]domain.SectorIntelligence, error)`

- [ ] **Step 1: Write unit test for SectorUsecase**

Create `backend/tests/sector_usecase_test.go`:
```go
package tests

import (
	"context"
	"testing"

	"be/internal/adapter/python_engine"
	"be/internal/domain"
	"be/internal/usecase"
)

func TestSectorUsecase_GetSectorAndList(t *testing.T) {
	// Uses client with offline fallback
	client := python_engine.NewClient("http://127.0.0.1:59999")
	uc := usecase.NewSectorUsecase(client)

	sec, err := uc.GetSectorIntelligence(context.Background(), "Financials")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if sec.Sector != "Financials" {
		t.Fatalf("expected Financials, got %s", sec.Sector)
	}

	list, err := uc.ListSectors(context.Background())
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(list) == 0 {
		t.Fatalf("expected non-empty sector list")
	}

	// Test invalid empty sector
	_, err = uc.GetSectorIntelligence(context.Background(), "")
	if err != domain.ErrInvalidSector {
		t.Fatalf("expected ErrInvalidSector, got %v", err)
	}
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `go test ./tests -run TestSectorUsecase_GetSectorAndList`
Expected: FAIL due to missing `usecase.NewSectorUsecase`.

- [ ] **Step 3: Create `backend/internal/usecase/sector_usecase.go`**

```go
package usecase

import (
	"context"
	"fmt"
	"strings"

	"be/internal/domain"
)

type SectorUsecase interface {
	GetSectorIntelligence(ctx context.Context, sectorName string) (*domain.SectorIntelligence, error)
	ListSectors(ctx context.Context) ([]domain.SectorIntelligence, error)
}

type SectorProvider interface {
	GetSectorIntelligence(ctx context.Context, sectorName string) (*domain.SectorIntelligence, error)
	ListSectorIntelligences(ctx context.Context) ([]domain.SectorIntelligence, error)
}

type sectorUsecase struct {
	provider SectorProvider
}

func NewSectorUsecase(provider SectorProvider) SectorUsecase {
	return &sectorUsecase{provider: provider}
}

func (u *sectorUsecase) GetSectorIntelligence(ctx context.Context, sectorName string) (*domain.SectorIntelligence, error) {
	cleanName := strings.TrimSpace(sectorName)
	if cleanName == "" {
		return nil, domain.ErrInvalidSector
	}

	sec, err := u.provider.GetSectorIntelligence(ctx, cleanName)
	if err != nil {
		return nil, fmt.Errorf("sectorUsecase.GetSectorIntelligence: %w", err)
	}
	return sec, nil
}

func (u *sectorUsecase) ListSectors(ctx context.Context) ([]domain.SectorIntelligence, error) {
	list, err := u.provider.ListSectorIntelligences(ctx)
	if err != nil {
		return nil, fmt.Errorf("sectorUsecase.ListSectors: %w", err)
	}
	return list, nil
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `go test ./tests -run TestSectorUsecase_GetSectorAndList -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add internal/usecase/sector_usecase.go tests/sector_usecase_test.go
git commit -m "feat(usecase): add sector intelligence usecase"
```

---

### Task 4: HTTP Delivery Handler, Routing, and Dependency Injection

**Files:**
- Create: `backend/internal/delivery/http/handler/sector_handler.go`
- Modify: `backend/internal/delivery/http/router.go:1-55`
- Modify: `backend/cmd/api/main.go:1-120`
- Test: `backend/tests/sector_api_test.go`

**Interfaces:**
- Produces:
  - `GET /api/v1/sectors`
  - `GET /api/v1/sectors/{sector}`
  - Updated `GET /api/v1/companies/{symbol}/intelligence` returning `smart_money` and `catalysts`

- [ ] **Step 1: Write integration test for HTTP endpoints**

Create `backend/tests/sector_api_test.go`:
```go
package tests

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"be/internal/adapter/python_engine"
	appHttp "be/internal/delivery/http"
	"be/internal/delivery/http/handler"
	"be/internal/platform/logger"
	"be/internal/repository/memory"
	"be/internal/usecase"
)

func setupTestApp() http.Handler {
	log := logger.New("info")
	pyClient := python_engine.NewClient("http://127.0.0.1:59999") // offline fallback
	companyRepo := memory.NewCompanyRepository()

	compUc := usecase.NewCompanyUsecase(companyRepo)
	intelUc := usecase.NewIntelligenceUsecase(pyClient)
	scannerUc := usecase.NewScannerUsecase(companyRepo, pyClient)
	analyticsUc := usecase.NewAnalyticsUsecase(companyRepo)
	sectorUc := usecase.NewSectorUsecase(pyClient)

	handlers := appHttp.Handlers{
		Health:       handler.NewHealthHandler(),
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

	if resp["smart_money"] == nil {
		t.Fatalf("expected smart_money in response, got nil")
	}
	if resp["catalysts"] == nil {
		t.Fatalf("expected catalysts in response, got nil")
	}
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `go test ./tests -run TestSectorEndpoints`
Expected: FAIL due to missing `handler.NewSectorHandler` and `handlers.Sector`.

- [ ] **Step 3: Create `handler/sector_handler.go`, update `router.go` and `cmd/api/main.go`**

Create `backend/internal/delivery/http/handler/sector_handler.go`:
```go
package handler

import (
	"encoding/json"
	"errors"
	"net/http"

	"be/internal/domain"
	"be/internal/usecase"
)

type SectorHandler struct {
	sectorUsecase usecase.SectorUsecase
}

func NewSectorHandler(sectorUsecase usecase.SectorUsecase) *SectorHandler {
	return &SectorHandler{sectorUsecase: sectorUsecase}
}

func (h *SectorHandler) GetSector(w http.ResponseWriter, r *http.Request) {
	sectorName := r.PathValue("sector")
	sec, err := h.sectorUsecase.GetSectorIntelligence(r.Context(), sectorName)
	if err != nil {
		if errors.Is(err, domain.ErrInvalidSector) || errors.Is(err, domain.ErrSectorNotFound) {
			renderError(w, http.StatusNotFound, err.Error())
			return
		}
		renderError(w, http.StatusInternalServerError, err.Error())
		return
	}

	renderJSON(w, http.StatusOK, sec)
}

func (h *SectorHandler) ListSectors(w http.ResponseWriter, r *http.Request) {
	sectors, err := h.sectorUsecase.ListSectors(r.Context())
	if err != nil {
		renderError(w, http.StatusInternalServerError, err.Error())
		return
	}

	renderJSON(w, http.StatusOK, map[string]any{
		"sectors": sectors,
		"count":   len(sectors),
	})
}
```

Update `backend/internal/delivery/http/router.go`:
- Add `Sector *handler.SectorHandler` to `Handlers` struct.
- Add routes:
  - `mux.HandleFunc("GET /api/v1/sectors", handlers.Sector.ListSectors)`
  - `mux.HandleFunc("GET /api/v1/sectors/{sector}", handlers.Sector.GetSector)`

Update `backend/cmd/api/main.go`:
- Instantiate `sectorUsecase := usecase.NewSectorUsecase(pyEngineClient)`
- Pass `Sector: handler.NewSectorHandler(sectorUsecase)` into `Handlers`.

- [ ] **Step 4: Run all tests in `tests/`**

Run: `go test ./tests/... -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add internal/delivery/http/handler/sector_handler.go internal/delivery/http/router.go cmd/api/main.go tests/sector_api_test.go
git commit -m "feat(api): expose sector intelligence endpoints and enriched company intelligence"
```

---

### Task 5: End-to-End Verification & Health Check

**Files:**
- Test: All tests across `tests/`
- Build verification: `go build ./cmd/api`

- [ ] **Step 1: Run full test suite with race detector**

Run: `go test -v -race ./tests/...`
Expected: PASS with 0 data races.

- [ ] **Step 2: Build executable to verify compilation**

Run: `go build -o bin/api.exe ./cmd/api`
Expected: Exit code 0, binary created.

- [ ] **Step 3: Verification commit & summary**

```bash
git commit --allow-empty -m "chore(backend): verify full test suite and clean architecture compliance"
```
