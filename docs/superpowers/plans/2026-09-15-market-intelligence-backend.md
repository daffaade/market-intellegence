# Market Intelligence Platform — Go Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Membangun backend service Go dengan Clean Architecture untuk platform Market Intelligence IHSG yang mengorkestrasi PostgreSQL (sqlc/pgx), Python Intelligence Engine, dan Multi-Provider AI Explanation (Gemini 3+/Groq/Mock), lengkap dengan proteksi kuota 1.000 Sectors API credits.

**Architecture:** Menggunakan standard Go Clean Architecture (`internal/domain`, `internal/usecase`, `internal/repository`, `internal/adapter`, `internal/delivery`). Backend bertindak sebagai central orchestrator dengan caching agresif (TTL 24 jam) di PostgreSQL, komunikasi HTTP REST dengan timeout ketat (5s) ke Python FastAPI, dan prompting berpagar (*fact-grounded*) ke LLM untuk AI Research Summary tanpa rekomendasi investasi personal.

**Tech Stack:** Go 1.22+, PostgreSQL 15+, `github.com/jackc/pgx/v5`, `sqlc`, standard library `net/http` ServeMux, `log/slog`, REST JSON API.

## Global Constraints

- Domain Purity: `internal/domain` dilarang mengimpor library luar (tanpa database driver `pgx`, tanpa HTTP router/framework).
- Accept Interfaces, Return Structs: Usecase hanya bergantung pada domain interfaces.
- Zero-Quota-Wasted: Selalu cek cache PostgreSQL sebelum memanggil Sectors API; sediakan flag `MOCK_SECTORS=true` untuk fallback data lokal 5 emiten (`BBCA`, `AMRT`, `TLKM`, `ASII`, `GOTO`) dari folder `../market-intellegence/y_finance_data/`.
- Anti-Hallucination & Legal Disclaimer: LLM hanya merangkum `factors` dan `evidence` yang diberikan tanpa membuat angka baru, dan setiap respon intelijen wajib menyertakan klausul disclaimer resmi.
- Concurrency Safety: Semua outbound I/O (Sectors API, Python Engine, LLM) wajib memakai `context.WithTimeout`; batch processing scanner menggunakan bounded worker pool (maks 4 worker).

---

### Task 1: Project Scaffolding, Go Module & Configuration

**Files:**
- Create: `go.mod`
- Create: `internal/platform/config/config.go`
- Create: `internal/platform/logger/logger.go`
- Create: `.env.example`
- Test: `tests/platform_test.go`

**Interfaces:**
- Produces: `config.Config`, `config.LoadConfig() (*Config, error)`, `logger.InitLogger(level string) *slog.Logger`

- [ ] **Step 1: Inisialisasi go.mod dan dependency dasar**
```bash
go mod init be
go get github.com/jackc/pgx/v5
go get github.com/joho/godotenv
```

- [ ] **Step 2: Tulis test untuk configuration loader**
Buat `tests/platform_test.go`:
```go
package tests

import (
	"os"
	"testing"

	"be/internal/platform/config"
)

func testPlatformConfig(t *testing.T) {
	os.Setenv("PORT", "9090")
	os.Setenv("MOCK_SECTORS", "true")
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
}
```

- [ ] **Step 3: Implementasi Config & Logger**
Buat `internal/platform/config/config.go` dan `internal/platform/logger/logger.go`:
```go
package config

import (
	"os"
	"strconv"
)

type Config struct {
	Port              string
	DatabaseURL       string
	PythonEngineURL   string
	SectorsAPIKey     string
	SectorsBaseURL    string
	MockSectors       bool
	AIProvider        string // "gemini", "groq", "mock"
	AIModel           string // "gemini-3.5-flash", "llama-3.3-70b-versatile"
	AIApiKey          string
	CacheTTLHours     int
}

func LoadConfig() (*Config, error) {
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
```

- [ ] **Step 4: Jalankan test verifikasi Task 1**
Run: `go test -v ./tests/... -run TestPlatformConfig`
Expected: PASS

- [ ] **Step 5: Commit Task 1**
```bash
git add go.mod go.sum internal/platform/ .env.example tests/
git commit -m "feat: scaffold project, config loader, and structured logger"
```

---

### Task 2: Pure Domain Layer Entities & Interfaces

**Files:**
- Create: `internal/domain/company.go`
- Create: `internal/domain/intelligence.go`
- Create: `internal/domain/ai_summary.go`
- Create: `internal/domain/repository.go`
- Create: `internal/domain/intelligence_client.go`
- Create: `internal/domain/ai_client.go`
- Create: `internal/domain/errors.go`
- Test: `tests/domain_test.go`

**Interfaces:**
- Produces: `Company`, `FinancialSnapshot`, `IntelligenceSnapshot`, `WhatChangedItem`, `PeerComparisonItem`, `EvidenceItem`, `CompanyRepository`, `SnapshotRepository`, `IntelligenceEngineClient`, `AIExplanationClient`

- [ ] **Step 1: Definisikan domain errors dan pure entities**
Buat `internal/domain/errors.go`:
```go
package domain

import "errors"

var (
	ErrCompanyNotFound    = errors.New("company not found")
	ErrInvalidSymbol      = errors.New("invalid stock symbol")
	ErrUpstreamTimeout    = errors.New("upstream service timed out")
	ErrQuotaExceeded      = errors.New("sectors api quota exceeded")
	ErrIntelligenceFailed = errors.New("failed to compute intelligence")
)
```

Buat `internal/domain/company.go`:
```go
package domain

import "time"

type Company struct {
	Symbol    string    `json:"symbol"`
	Name      string    `json:"name"`
	Sector    string    `json:"sector"`
	SubSector string    `json:"sub_sector"`
	MarketCap int64     `json:"market_cap"`
	UpdatedAt time.Time `json:"updated_at"`
}

type FinancialSnapshot struct {
	Symbol            string                 `json:"symbol"`
	SnapshotDate      time.Time              `json:"snapshot_date"`
	ValuationMetrics  map[string]interface{} `json:"valuation_metrics"`
	Financials        map[string]interface{} `json:"financials"`
	InstitutionalFlow map[string]interface{} `json:"institutional_flow"`
	RawPayload        map[string]interface{} `json:"raw_payload"`
	FetchedAt         time.Time              `json:"fetched_at"`
}
```

Buat `internal/domain/intelligence.go`:
```go
package domain

import "time"

type EvidenceItem struct {
	Metric       string `json:"metric"`
	CompanyValue string `json:"company_value"`
	PeerMedian   string `json:"peer_median"`
	Position     string `json:"position"`
}

type WhatChangedItem struct {
	Metric   string `json:"metric"`
	Previous string `json:"previous"`
	Current  string `json:"current"`
	Delta    string `json:"delta"`
	Impact   string `json:"impact"`
}

type PeerComparisonItem struct {
	Metric     string `json:"metric"`
	Target     string `json:"target"`
	PeerMedian string `json:"peer_median"`
	Position   string `json:"position"`
}

type IntelligenceSnapshot struct {
	ID                 int64                `json:"id"`
	Symbol             string               `json:"symbol"`
	OpportunityScore   float64              `json:"opportunity_score"`
	RiskScore          float64              `json:"risk_score"`
	Direction          string               `json:"direction"`
	Confidence         string               `json:"confidence"`
	RiskLevel          string               `json:"risk_level"`
	IsAnomaly          bool                 `json:"is_anomaly"`
	AnomalyScore       float64              `json:"anomaly_score"`
	DivergenceDetected bool                 `json:"divergence_detected"`
	PositiveFactors    []string             `json:"positive_factors"`
	NegativeFactors    []string             `json:"negative_factors"`
	SupportingFactors  []string             `json:"supporting_factors"`
	Evidence           []EvidenceItem       `json:"evidence"`
	WhatChanged        []WhatChangedItem    `json:"what_changed"`
	PeerComparison     []PeerComparisonItem `json:"peer_comparison"`
	AIResearchSummary  string               `json:"ai_research_summary"`
	Disclaimer         string               `json:"disclaimer"`
	IsCached           bool                 `json:"is_cached"`
	CreatedAt          time.Time            `json:"created_at"`
}
```

Buat `internal/domain/repository.go` dan domain client interfaces:
```go
package domain

import "context"

type CompanyRepository interface {
	GetBySymbol(ctx context.Context, symbol string) (*Company, error)
	ListAll(ctx context.Context) ([]Company, error)
	ListBySector(ctx context.Context, sector string) ([]Company, error)
	Upsert(ctx context.Context, comp *Company) error
}

type SnapshotRepository interface {
	GetLatestIntelligence(ctx context.Context, symbol string) (*IntelligenceSnapshot, error)
	SaveIntelligence(ctx context.Context, snap *IntelligenceSnapshot) error
	GetLatestSectorsData(ctx context.Context, symbol string) (*FinancialSnapshot, error)
	SaveSectorsData(ctx context.Context, snap *FinancialSnapshot) error
	GetTopOpportunities(ctx context.Context, limit int) ([]IntelligenceSnapshot, error)
	GetTopRisks(ctx context.Context, limit int) ([]IntelligenceSnapshot, error)
	GetRecentAnomalies(ctx context.Context, limit int) ([]IntelligenceSnapshot, error)
}
```

- [ ] **Step 2: Tulis unit test untuk verifikasi domain struct**
Buat `tests/domain_test.go`:
```go
package tests

import (
	"testing"
	"be/internal/domain"
)

func TestDomainStructures(t *testing.T) {
	snap := domain.IntelligenceSnapshot{
		Symbol:           "BBCA",
		OpportunityScore: 84.5,
		Direction:        "Bullish",
		Confidence:       "High",
	}
	if snap.Symbol != "BBCA" || snap.OpportunityScore != 84.5 {
		t.Errorf("domain struct mismatch: %+v", snap)
	}
}
```

- [ ] **Step 3: Run test & commit Task 2**
Run: `go test -v ./tests/... -run TestDomainStructures`
```bash
git add internal/domain/ tests/domain_test.go
git commit -m "feat: define domain entities, sentinel errors, and repository interfaces"
```

---

### Task 3: PostgreSQL Schema, Migrations & SQLC Setup

**Files:**
- Create: `sqlc.yaml`
- Create: `db/migrations/000001_init_schema.up.sql`
- Create: `db/migrations/000001_init_schema.down.sql`
- Create: `db/queries/companies.sql`
- Create: `db/queries/intelligence.sql`
- Output: `db/sqlc/` (generated)

- [ ] **Step 1: Tulis SQL Migrasi Up dan Down**
Tulis `db/migrations/000001_init_schema.up.sql` sesuai spesifikasi Bagian 4.
Tulis `db/migrations/000001_init_schema.down.sql`:
```sql
DROP TABLE IF EXISTS intelligence_snapshots;
DROP TABLE IF EXISTS sectors_data_snapshots;
DROP TABLE IF EXISTS companies;
```

- [ ] **Step 2: Tulis Query SQL untuk sqlc di `db/queries/`**
`db/queries/companies.sql`:
```sql
-- name: GetCompany :one
SELECT symbol, name, sector, sub_sector, market_cap, created_at, updated_at
FROM companies WHERE symbol = $1 LIMIT 1;

-- name: ListCompanies :many
SELECT symbol, name, sector, sub_sector, market_cap, created_at, updated_at
FROM companies ORDER BY symbol ASC;

-- name: UpsertCompany :one
INSERT INTO companies (symbol, name, sector, sub_sector, market_cap, updated_at)
VALUES ($1, $2, $3, $4, $5, NOW())
ON CONFLICT (symbol) DO UPDATE SET
    name = EXCLUDED.name,
    sector = EXCLUDED.sector,
    sub_sector = EXCLUDED.sub_sector,
    market_cap = EXCLUDED.market_cap,
    updated_at = NOW()
RETURNING *;
```

`db/queries/intelligence.sql`:
```sql
-- name: GetLatestIntelligence :one
SELECT * FROM intelligence_snapshots
WHERE symbol = $1
ORDER BY created_at DESC
LIMIT 1;

-- name: InsertIntelligenceSnapshot :one
INSERT INTO intelligence_snapshots (
    symbol, opportunity_score, risk_score, direction, confidence, risk_level,
    is_anomaly, anomaly_score, divergence_detected, positive_factors, negative_factors,
    supporting_factors, evidence, ai_research_summary, model_version, created_at
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, NOW()
)
RETURNING *;

-- name: GetTopOpportunities :many
SELECT * FROM intelligence_snapshots
ORDER BY opportunity_score DESC, created_at DESC
LIMIT $1;

-- name: GetTopRisks :many
SELECT * FROM intelligence_snapshots
ORDER BY risk_score DESC, created_at DESC
LIMIT $1;

-- name: GetRecentAnomalies :many
SELECT * FROM intelligence_snapshots
WHERE is_anomaly = true OR divergence_detected = true
ORDER BY created_at DESC
LIMIT $1;
```

- [ ] **Step 3: Setup `sqlc.yaml`**
```yaml
version: "2"
sql:
  - engine: "postgresql"
    schema: "db/migrations"
    queries: "db/queries"
    gen:
      go:
        package: "sqlc"
        out: "db/sqlc"
        sql_package: "pgx/v5"
        emit_json_tags: true
        emit_interface: true
        emit_empty_slices: true
```

- [ ] **Step 4: Generate SQLC dan Commit Task 3**
```bash
git add sqlc.yaml db/
git commit -m "feat: setup database schema migrations and sqlc queries"
```

---

### Task 4: PostgreSQL Repository Implementation (`sqlc` + `pgx/v5`)

**Files:**
- Create: `internal/repository/postgres/pool.go`
- Create: `internal/repository/postgres/company_repo.go`
- Create: `internal/repository/postgres/snapshot_repo.go`
- Test: `tests/repository_test.go`

**Interfaces:**
- Implements: `domain.CompanyRepository`, `domain.SnapshotRepository`

- [ ] **Step 1: Implementasi Connection Pool dengan `pgxpool.Pool`**
Buat `internal/repository/postgres/pool.go` sesuai best practice `sqlc-pgx-expert` (MaxConns=25, MinConns=5, MaxConnLifetime=1h).

- [ ] **Step 2: Implementasi Repository Adapters**
Bungkus query sqlc ke dalam `company_repo.go` dan `snapshot_repo.go`. Lakukan deserialisasi JSONB column (`evidence`, `factors`) ke struct domain murni.

- [ ] **Step 3: Test Repository / Mock Test**
Verifikasi error mapping ketika row tidak ditemukan ke `domain.ErrCompanyNotFound`.

- [ ] **Step 4: Commit Task 4**
```bash
git add internal/repository/ tests/repository_test.go
git commit -m "feat: implement postgres repository with pgxpool and sqlc mapping"
```

---

### Task 5: Python Engine Adapter (FastAPI Client) & Concurrency Guard

**Files:**
- Create: `internal/adapter/python_engine/client.go`
- Test: `tests/python_engine_test.go`

**Interfaces:**
- Implements: `domain.IntelligenceEngineClient`

- [ ] **Step 1: Tulis unit test dengan httptest.Server**
Buat `tests/python_engine_test.go` yang mensimulasikan server FastAPI mengembalikan payload Prototype 3 JSON dan tes skenario timeout.

- [ ] **Step 2: Implementasi Python Engine Client**
Buat `internal/adapter/python_engine/client.go`:
- HTTP Client dengan reuse connection pool (`Transport`).
- Membaca `POST /api/v1/analyze`.
- Menerapkan `context.WithTimeout(ctx, 5*time.Second)`.
- Memetakan JSON response ke `domain.IntelligenceSnapshot`.

- [ ] **Step 3: Run test & commit Task 5**
Run: `go test -v ./tests/... -run TestPythonEngine`
```bash
git add internal/adapter/python_engine/ tests/python_engine_test.go
git commit -m "feat: implement python fastapi client with timeout and context cancellation"
```

---

### Task 6: Multi-Provider AI Explanation Layer (Gemini 3+, Groq & Mock)

**Files:**
- Create: `internal/adapter/llm/gemini.go`
- Create: `internal/adapter/llm/groq.go`
- Create: `internal/adapter/llm/mock.go`
- Create: `internal/adapter/llm/factory.go`
- Test: `tests/llm_test.go`

**Interfaces:**
- Implements: `domain.AIExplanationClient`

- [ ] **Step 1: Tulis unit test untuk Mock Rule Synthesizer**
Pastikan Mock Synthesizer menghasilkan paragraf riset berbasis evidence tanpa bergantung pada network atau API key.

- [ ] **Step 2: Implementasi Factory & Providers**
- `mock.go`: Menghasilkan analisis riset deterministik berdasarkan `positive_factors` dan `evidence`.
- `gemini.go`: Menembak endpoint Google Gemini API (model konfigurasi: `gemini-3.5-flash` atau `gemini-2.5-flash`) dengan strict fact-grounded system instruction.
- `groq.go`: Menembak endpoint Groq OpenAI-compatible gratis (`https://api.groq.com/openai/v1/chat/completions`).

- [ ] **Step 3: Run test & commit Task 6**
Run: `go test -v ./tests/... -run TestLLMSynthesizer`
```bash
git add internal/adapter/llm/ tests/llm_test.go
git commit -m "feat: implement multi-provider ai explanation layer with gemini 3+ and offline mock"
```

---

### Task 7: Sectors API Adapter & Zero-Quota Local Seeder

**Files:**
- Create: `internal/adapter/sectors_api/client.go`
- Create: `internal/adapter/sectors_api/mock_seeder.go`
- Test: `tests/sectors_test.go`

**Interfaces:**
- Produces: `FetchCompanyFinancials(ctx, symbol)`, `SeedFromLocalData(ctx)`

- [ ] **Step 1: Tulis unit test untuk Mock Seeder**
Memverifikasi bahwa parser dapat membaca data dari `../market-intellegence/y_finance_data/{ticker}.csv` jika `MOCK_SECTORS=true`.

- [ ] **Step 2: Implementasi Sectors API Client & Mock Seeder**
- Jika `SECTORS_API_KEY` terpasang dan `MOCK_SECTORS=false`, request ke REST API Sectors.
- Jika offline/mock, baca CSV lokal untuk 5 emiten (`BBCA`, `AMRT`, `TLKM`, `ASII`, `GOTO`) dan bentuk struct finansial.

- [ ] **Step 3: Run test & commit Task 7**
Run: `go test -v ./tests/... -run TestSectorsAdapter`
```bash
git add internal/adapter/sectors_api/ tests/sectors_test.go
git commit -m "feat: implement sectors api client with credit-safe local csv seeder"
```

---

### Task 8: Business Usecase Layer Orchestration

**Files:**
- Create: `internal/usecase/company_usecase.go`
- Create: `internal/usecase/intelligence_usecase.go`
- Create: `internal/usecase/scanner_usecase.go`
- Test: `tests/usecase_test.go`

**Interfaces:**
- Produces: `CompanyUsecase`, `IntelligenceUsecase`, `ScannerUsecase`

- [ ] **Step 1: Tulis unit test orkestrasi dengan Mock Repository & Clients**
Uji skenario:
1. Cache Hit (<24 jam) -> Langsung return data DB tanpa panggil Sectors/Python/LLM.
2. Cache Miss -> Panggil Data -> Python Engine -> LLM -> Simpan ke DB -> Return.
3. Python Engine Down -> Fallback aman ke cached snapshot atau mock tanpa return error 500.

- [ ] **Step 2: Implementasi Usecases**
- `intelligence_usecase.go`: Menghubungkan seluruh alur pipeline dan menyematkan disclaimer resmi:
  > *"Informasi dan analisis ini merupakan hasil pemrosesan data riset dan bukan merupakan anjuran investasi personal (Bukan rekomendasi Beli/Jual)."*
- `scanner_usecase.go`: Worker pool 4 goroutine paralel untuk filtering dan ranking multi-emiten.

- [ ] **Step 3: Run test & commit Task 8**
Run: `go test -v ./tests/... -run TestIntelligenceUsecase`
```bash
git add internal/usecase/ tests/usecase_test.go
git commit -m "feat: implement intelligence orchestration usecase with caching and worker pools"
```

---

### Task 9: Delivery Layer: DTOs, Handlers, CORS & Router

**Files:**
- Create: `internal/delivery/http/dto/response.go`
- Create: `internal/delivery/http/middleware/cors.go`
- Create: `internal/delivery/http/middleware/logger.go`
- Create: `internal/delivery/http/handler/company_handler.go`
- Create: `internal/delivery/http/handler/intelligence_handler.go`
- Create: `internal/delivery/http/handler/scanner_handler.go`
- Create: `internal/delivery/http/handler/health_handler.go`
- Create: `internal/delivery/http/router.go`
- Test: `tests/delivery_test.go`

- [ ] **Step 1: Tulis HTTP Handler Tests dengan `net/http/httptest`**
Uji endpoint:
- `GET /api/v1/health` -> HTTP 200 `{ "status": "ok" }`
- `GET /api/v1/companies/BBCA/intelligence` -> HTTP 200 with structured JSON and disclaimer
- `GET /api/v1/market/overview` -> HTTP 200

- [ ] **Step 2: Implementasi Handlers & Router**
- Standar Go 1.22+ `http.NewServeMux` dengan path pattern routing (`GET /api/v1/companies/{symbol}/intelligence`).
- Middleware CORS (mendukung origin `http://localhost:1420` dan `tauri://localhost`).
- Response wrapper terstandar: `{ "status": "success", "data": ... }`.

- [ ] **Step 3: Run test & commit Task 9**
Run: `go test -v ./tests/... -run TestHTTPDelivery`
```bash
git add internal/delivery/ tests/delivery_test.go
git commit -m "feat: implement http handlers, dtos, cors middleware, and routes"
```

---

### Task 10: Composition Root (`cmd/api/main.go`), Makefile & Verification

**Files:**
- Create: `cmd/api/main.go`
- Create: `Makefile`
- Create: `README.md`

- [ ] **Step 1: Tulis `cmd/api/main.go`**
- Load config.
- Inisialisasi Logger (`log/slog`).
- Inisialisasi Database Connection Pool / In-Memory Mock Fallback.
- Wire adapters (Sectors, Python Engine, AI Provider).
- Wire usecases.
- Wire HTTP handlers & router.
- Graceful shutdown server via `os.Interrupt` / `syscall.SIGTERM`.

- [ ] **Step 2: Tulis `Makefile` dan dokumentasi `README.md`**
Target: `make run`, `make test`, `make build`, `make seed`.

- [ ] **Step 3: Verifikasi Kompilasi & Jalankan Server Sanity Check**
Run: `go build -o bin/api.exe ./cmd/api`
Run: `go test -v ./...`
Expected: Seluruh unit test PASS dan binary berhasil dibuild tanpa error.

- [ ] **Step 4: Commit Task 10**
```bash
git add cmd/ Makefile README.md
git commit -m "feat: wire composition root, graceful shutdown, makefile, and docs"
```
