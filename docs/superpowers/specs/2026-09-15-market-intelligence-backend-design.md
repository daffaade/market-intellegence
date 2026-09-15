# Market Intelligence Platform — Go Backend Design Specification

- **Project:** Sectors Hackathon Indonesia 2026 (Track 03 — Market Intelligence)
- **Role:** Backend Engineer (Go)
- **Author:** Antigravity & Backend Engineer
- **Date:** 2026-09-15
- **Status:** Approved / In Review

---

## 1. Executive Summary & Context

Sistem ini adalah backend berperforma tinggi yang dibangun menggunakan **Golang** dengan arsitektur **Clean Architecture**. Sistem bertindak sebagai **Central Orchestrator** dalam platform *AI-Powered Market Intelligence* untuk pasar saham Indonesia (IHSG).

### Prinsip Utama
1. **Sectors API as Core Data Source:** Data finansial utama bersumber dari Sectors REST API/MCP.
2. **Deterministic Intelligence First:** Kalkulasi intelijen (skor peluang, risiko, anomali, divergensi, perubahan) dihitung secara deterministik dan berbasis data (didukung Python Engine), bukan dihitung oleh LLM.
3. **Evidence-Based & Explainable:** Setiap skor dan sinyal wajib memiliki bukti (*evidence*) data pendukung yang transparan.
4. **AI as Explanation Layer Only:** LLM (Google Gemini 3+/3.5 Flash, Groq, atau Mock) bertindak murni sebagai generator rangkuman riset berbasis bukti tanpa halusinasi dan **tanpa anjuran investasi personal (BUY/HOLD/SELL)**.
5. **Zero-Failure Demo & Credit Protection:** Melindungi kuota terbatas **1.000 Sectors API credits** dengan snapshot caching 24 jam di PostgreSQL dan fallback data seeding lokal (5 emiten: BBCA, AMRT, TLKM, ASII, GOTO).

---

## 2. System Architecture & Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│               Frontend: React + TypeScript + Tauri          │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP REST JSON (CORS enabled)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     Go Backend (Clean Arch)                 │
│                                                             │
│   [Delivery] HTTP Handlers (net/http ServeMux / Chi)        │
│        ↓                                                    │
│   [Usecase]  Company, Intelligence, Scanner, Fallback       │
│        ↓                                                    │
│   [Domain]   Pure Entities, Repository & Client Interfaces  │
│        ↓                                                    │
│   [Adapters & Repositories]                                 │
│      ├── PostgreSQL Repo (sqlc + pgx/v5)                    │
│      ├── Python FastAPI Client (POST /api/v1/analyze)       │
│      ├── Sectors API Client (with Rate Limiter & Cache)     │
│      └── AI Explanation Client (Gemini 3.5, Groq, Mock)     │
└───────┬──────────────────────┬──────────────────────┬───────┘
        │                      │                      │
        ▼                      ▼                      ▼
┌────────────────┐   ┌───────────────────┐  ┌─────────────────┐
│   PostgreSQL   │   │ Python FastAPI    │  │  AI Provider    │
│  (Data Cache & │   │ (Stacking ML &    │  │ (Gemini 3+/3.5, │
│   Snapshots)   │   │  IsolationForest) │  │  Groq, Mock)    │
└────────────────┘   └───────────────────┘  └─────────────────┘
```

---

## 3. Directory Layout (Golang Clean Architecture)

Sesuai standar `golang-clean-arch`:

```text
be/
├── cmd/
│   └── api/
│       └── main.go                 # Composition root: dependency injection & server run
├── internal/
│   ├── domain/                     # Pure domain logic, no external DB/framework imports
│   │   ├── company.go              # Entity: Company, FinancialMetrics, PeerComparison
│   │   ├── intelligence.go         # Entity: Signal, Anomaly, Score, Evidence, Divergence
│   │   ├── ai_summary.go           # Entity: AI Explanation & Prompts
│   │   ├── repository.go           # Domain interfaces for DB persistence
│   │   ├── intelligence_client.go  # Domain interface for Python Engine communication
│   │   ├── ai_client.go            # Domain interface for LLM calls
│   │   └── errors.go               # Sentinel errors (ErrNotFound, ErrUpstreamTimeout, etc.)
│   ├── usecase/                    # Application business rules & orchestration
│   │   ├── company_usecase.go      # Company profile & peer aggregation
│   │   ├── intelligence_usecase.go # Full intelligence pipeline orchestration
│   │   ├── scanner_usecase.go      # Intelligent screener & market overview ranking
│   │   └── mock_usecase.go         # Zero-credit offline fallback provider
│   ├── repository/
│   │   └── postgres/               # PostgreSQL implementation using sqlc + pgx/v5
│   │       ├── company_repo.go
│   │       ├── snapshot_repo.go
│   │       └── pool.go             # pgxpool.Pool setup
│   ├── adapter/
│   │   ├── python_engine/          # HTTP client for Python FastAPI
│   │   │   └── client.go
│   │   ├── sectors_api/            # HTTP client for Sectors API with rate limiting
│   │   │   └── client.go
│   │   └── llm/                    # Client for Gemini 3+/3.5, Groq, and Mock Synthesizer
│   │       ├── gemini.go
│   │       ├── groq.go
│   │       ├── mock.go
│   │       └── factory.go
│   ├── delivery/
│   │   └── http/                   # HTTP Transport Layer
│   │       ├── router.go
│   │       ├── middleware/         # Logger, CORS, Recovery, Request Timeout
│   │       ├── handler/
│   │       │   ├── company_handler.go
│   │       │   ├── intelligence_handler.go
│   │       │   ├── scanner_handler.go
│   │       │   └── health_handler.go
│   │       └── dto/                # Request & Response JSON serialization
│   └── platform/                   # Config, logging, concurrency guard utilities
│       ├── config/
│       └── logger/
├── db/
│   ├── migrations/                 # PostgreSQL migrations
│   │   ├── 000001_init_schema.up.sql
│   │   └── 000001_init_schema.down.sql
│   ├── queries/                    # SQL queries for sqlc
│   │   ├── companies.sql
│   │   └── intelligence_snapshots.sql
│   └── sqlc/                       # Auto-generated type-safe Go code
├── sqlc.yaml
├── go.mod
├── go.sum
└── Makefile
```

---

## 4. Database Schema & Persistence (`sqlc` + `pgx/v5`)

### Tables (`db/migrations/000001_init_schema.up.sql`)

```sql
-- 1. Master emiten & sektor
CREATE TABLE companies (
    symbol VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    sector VARCHAR(100) NOT NULL,
    sub_sector VARCHAR(100),
    market_cap BIGINT DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_companies_sector ON companies(sector);

-- 2. Snapshot Data Sectors API (Proteksi Kuota 1.000 Credits)
CREATE TABLE sectors_data_snapshots (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL REFERENCES companies(symbol) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
    valuation_metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    financials JSONB NOT NULL DEFAULT '{}'::jsonb,
    institutional_flow JSONB NOT NULL DEFAULT '{}'::jsonb,
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_sectors_symbol_date UNIQUE (symbol, snapshot_date)
);
CREATE INDEX idx_sectors_symbol_date ON sectors_data_snapshots(symbol, snapshot_date DESC);
CREATE INDEX idx_sectors_raw_gin ON sectors_data_snapshots USING gin(raw_payload);

-- 3. Output Intelligence Engine & AI Explanation
CREATE TABLE intelligence_snapshots (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL REFERENCES companies(symbol) ON DELETE CASCADE,
    opportunity_score NUMERIC(5, 2) NOT NULL,
    risk_score NUMERIC(5, 2) NOT NULL,
    direction VARCHAR(20) NOT NULL,
    confidence VARCHAR(20) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    is_anomaly BOOLEAN NOT NULL DEFAULT FALSE,
    anomaly_score NUMERIC(5, 2) DEFAULT 0,
    divergence_detected BOOLEAN NOT NULL DEFAULT FALSE,
    positive_factors JSONB NOT NULL DEFAULT '[]'::jsonb,
    negative_factors JSONB NOT NULL DEFAULT '[]'::jsonb,
    supporting_factors JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    ai_research_summary TEXT,
    model_version VARCHAR(50) NOT NULL DEFAULT 'v3-stacking-rf',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_intel_symbol_time ON intelligence_snapshots(symbol, created_at DESC);
CREATE INDEX idx_intel_scores ON intelligence_snapshots(opportunity_score DESC, risk_score ASC);
```

---

## 5. Integration Contracts & Protocols

### 5.1 Python FastAPI Engine (`POST /api/v1/analyze`)
- **Request (Go -> Python):**
  ```json
  {
    "symbol": "BBCA",
    "include_peer": true,
    "include_anomaly": true,
    "include_divergence": true
  }
  ```
- **Response (Python -> Go, matching Prototype 3 JSON):**
  ```json
  {
    "ticker": "BBCA",
    "intelligence_output": {
      "anomaly": false,
      "anomaly_score": 12.0,
      "direction": "Bullish",
      "score": 84.5,
      "confidence": "High",
      "risk": "Low",
      "positive_factors": ["Growth 18% outperforming peer median 9%", "PE 11x below peer median 16x"],
      "negative_factors": ["Dividend yield slightly lower"]
    },
    "fundamental_divergence": {
      "detected": true,
      "confidence": "Medium",
      "supporting_factors": ["Valuation compressed while growth forecast improved"]
    },
    "evidence": [
      {"metric": "Growth", "company_value": "18%", "peer_median": "9%", "position": "Outperform"},
      {"metric": "PE Ratio", "company_value": "11x", "peer_median": "16x", "position": "Cheaper"}
    ],
    "timestamp": "2026-09-15T13:45:00Z"
  }
  ```

### 5.2 AI Explanation Layer (LLM Synthesis)
- **Providers:**
  1. Google Gemini (`gemini-3.5-flash`, `gemini-3-flash`, `gemini-2.5-flash`)
  2. Groq (`llama-3.3-70b-versatile`, free tier compatible API)
  3. Mock Rule-Based Synthesizer (Offline, zero-cost, zero-latency)
- **Strict Prompting Guardrail:** Fact-grounded to `positive_factors`, `negative_factors`, and `evidence`. Persona analitis objektif tanpa kata Beli/Jual. Disertai klausa sangkalan/disclaimer.

### 5.3 REST API Endpoints (Go -> Frontend Tauri)
- `GET /api/v1/health`
- `GET /api/v1/market/overview`
- `GET /api/v1/companies`
- `GET /api/v1/companies/{symbol}`
- `GET /api/v1/companies/{symbol}/intelligence`
- `GET /api/v1/companies/{symbol}/anomalies`
- `GET /api/v1/companies/{symbol}/peers`
- `POST /api/v1/screener`

---

## 6. Concurrency & Reliability Guardrails (`go-concurrency-guard`)

1. **Context Timeouts:**
   - Sectors API: 5 detik.
   - Python Engine API: 5 detik.
   - LLM Explanation: 8 detik.
   - HTTP Server Read/Write: 15 detik.
2. **Circuit Breaker & Degraded Fallback:**
   - Jika Python Engine / Sectors API down atau timeout, Go otomatis menyajikan data snapshot terakhir dari database PostgreSQL dengan flag `"is_cached": true`.
3. **Bounded Scanner Worker Pool:**
   - Scanning multi-emiten dibatasi 4 goroutine worker secara paralel menggunakan `sync.WaitGroup` dan channel hasil.

---

## 7. Definition of Done (DoD) & Verification Plan

- [ ] Repository terinisialisasi bersih dengan Git dan `go.mod`.
- [ ] Migrasi database PostgreSQL berjalan lancar (`up` & `down`).
- [ ] SQLC meng-generate kode Go tanpa error.
- [ ] Mock data provider siap dengan 5 emiten benchmark (`BBCA`, `AMRT`, `TLKM`, `ASII`, `GOTO`).
- [ ] Unit test pada Usecase layer dengan mock interfaces passing 100%.
- [ ] Handler HTTP mengembalikan response format JSON standar sesuai kontrak.
- [ ] `go vet ./...` dan `golangci-lint` bersih tanpa violation.
