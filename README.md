# AI-Powered Market Intelligence Platform (Backend)
> **Track 03 — Market Intelligence | Sectors Hackathon Indonesia 2026**

Backend API service built in **Go (Golang 1.22+)** with **Clean Architecture** for real-time market intelligence, institutional flow anomaly detection, fundamental divergence screening, and automated research synthesis for Indonesian equities (IDX).

---

## 🏛️ Clean Architecture

```text
cmd/
 └── api/main.go               # Application entrypoint & dependency injection
internal/
 ├── domain/                   # Pure business entities & interfaces (Zero external imports)
 ├── usecase/                  # Business logic (Intelligence, Company, Scanner worker pool)
 ├── adapter/
 │    ├── python_engine/       # Python FastAPI client + Prototype 3 fallback heuristics
 │    └── llm/                 # Multi-provider AI (Gemini 3.5 Flash, Groq, Rule-based)
 ├── repository/
 │    ├── postgres/            # sqlc + pgx/v5 production pool repository
 │    └── memory/              # In-memory repository for zero-setup local dev/testing
 ├── delivery/
 │    └── http/                # REST handlers, DTO serializers, CORS middleware
 └── platform/
      ├── config/              # Environment config loader
      └── logger/              # slog structured logger
db/
 ├── migrations/               # PostgreSQL DDL migrations (golang-migrate)
 ├── queries/                  # Raw SQL queries for sqlc
 └── sqlc/                     # Generated type-safe Go database routines
tests/                         # Unit and End-to-End integration tests
```

---

## 🚀 Quick Start (Zero-Setup Mode)

The backend features an **automatic in-memory fallback**. If PostgreSQL is not running locally, the server immediately boots using pre-seeded IDX data (`BBCA`, `TLKM`, `AMRT`, `ASII`, `GOTO`), allowing frontend developers (Tauri/React) to develop instantly without configuring a database.

```bash
# Clone and enter directory
cd be

# Run directly (uses in-memory fallback if postgres is offline)
go run ./cmd/api
```

The server will listen at `http://localhost:8080`.

---

## 📡 API Endpoints

All responses follow the standard JSON envelope: `{ "status": "success", "data": ... }`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | System health, active AI provider, and mock flags |
| `GET` | `/api/v1/market/overview` | Market summary: Top opportunities, top risks, detected anomalies |
| `POST` | `/api/v1/screener` | Filter emiten by sector, min opportunity, max risk, and divergence |
| `GET` | `/api/v1/companies` | List all tracked IDX companies |
| `GET` | `/api/v1/companies/{symbol}` | Get company profile and sector metadata |
| `GET` | `/api/v1/companies/{symbol}/intelligence` | Full AI intelligence snapshot, metrics, and synthesis |
| `GET` | `/api/v1/companies/{symbol}/anomalies` | Specific anomaly scores, divergence flags, and metrics |
| `GET` | `/api/v1/companies/{symbol}/peers` | Peer comparison against sector median |

---

## ⚖️ Hackathon Compliance & Anti-Halusinasi

1. **Non-Advisory Strict Compliance**:
   - The engine **never** outputs direct investment advice (NO BUY / HOLD / SELL recommendations).
   - Responses output objective market signatures: Direction (`Bullish` / `Bearish` / `Neutral`), Opportunity Score, Risk Level, and Divergence Signals.
   - Every intelligence response contains the mandatory compliance disclaimer:
     > *"Informasi dan analisis ini merupakan hasil pemrosesan data riset dan bukan merupakan anjuran investasi personal (Bukan rekomendasi Beli/Jual)."*

2. **Zero-Quota-Wasted Strategy**:
   - Database/memory caching with configurable TTL (`CACHE_TTL_HOURS`, default 24h). Repeated requests return cached snapshots in `<5ms` without expending Sectors API credits.

3. **Grounding & Fallback Safeguards**:
   - Multi-provider LLM prompts use low temperature (`0.2`) strictly grounded to verified metric values.
   - If Python engine or AI providers are offline, deterministic Prototype 3 heuristics ensure zero demo downtime.

---

## ⚙️ Configuration (`.env`)

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8080` | HTTP port |
| `DATABASE_URL` | `postgres://postgres:postgres@localhost:5432/market_intel?sslmode=disable` | PostgreSQL connection string |
| `PYTHON_ENGINE_URL` | `http://localhost:8000` | Python FastAPI Intelligence Engine URL |
| `SECTORS_API_KEY` | - | Sectors API key |
| `MOCK_SECTORS` | `false` | Enable Sectors API mock mode |
| `AI_PROVIDER` | `mock` | `mock`, `gemini`, or `groq` |
| `AI_MODEL` | `gemini-3.5-flash` | LLM model identifier |
| `AI_API_KEY` | - | Google Gemini or Groq API Key |
| `CACHE_TTL_HOURS` | `24` | Snapshot cache expiration in hours |
| `LOG_LEVEL` | `info` | Logging level (`debug`, `info`, `warn`, `error`) |

---

## 🧪 Testing

```bash
# Run all unit and integration tests
go test -v ./tests/...

# Run static analysis
go vet ./...
```
