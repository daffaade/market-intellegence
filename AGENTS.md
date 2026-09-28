# AGENTS.md — Master Project Guidelines & Context
> **Track 03: Market Intelligence | Sectors Hackathon Indonesia 2026**  
> AI-Powered Market Intelligence Platform for Indonesian Equities (IDX).

---

## 🎯 1. Mission & Domain Context

You are pair-programming with the development team on the **AI-Powered Market Intelligence Platform**.
The platform ingests Indonesian equities data, detects institutional flow anomalies, computes fundamental divergences, forecasts multi-horizon returns, synthesizes explainable research with LLMs, and serves results to a desktop app (Tauri + React).

### Key Emiten Tracked (Primary Universe):
`BBCA`, `BBRI`, `BMRI`, `BBNI`, `TLKM`, `ASII`, `AMRT`, `GOTO`, `ANTM`, `BUMI`.

---

## 🏛️ 2. Repository Architecture & Services

The repository is organized into modular services:

```text
market-intellegence/
 ├── data_processing/         # Data Ingestion & Normalization
 │    ├── data_sectors/       # Sectors API miner, normalizer, and cache
 │    ├── y_finance_data/     # YFinance historical price data & scrapers
 │    └── endpoint_finaldata.py
 │
 ├── ai_engine/               # Python AI & Machine Learning Service (FastAPI)
 │    ├── main.py             # Entrypoint on port 8000 (uvicorn main:app --port 8000)
 │    ├── models/forecast/    # Multi-Horizon Random Forest (H+1 .. H+7) & Signals
 │    ├── models/anomaly/     # Isolation Forest Anomaly Detection
 │    ├── models/peers/       # Peer Analysis & What-Changed detection
 │    └── routers/analyze.py  # Endpoint: POST /api/v1/analyze
 │
 ├── backend/                 # Go REST API Service (Clean Architecture)
 │    ├── cmd/api/main.go     # Entrypoint on port 8080 (go run ./cmd/api)
 │    ├── internal/domain/    # Pure entities & interfaces (Zero external imports)
 │    ├── internal/usecase/   # Intelligence, Company, and Scanner (Worker pool)
 │    ├── internal/adapter/   # Python engine HTTP client & Multi-provider LLM (Gemini/Groq/Rule)
 │    ├── internal/repository/# Dual-mode: PostgreSQL (sqlc) + In-memory fallback
 │    └── internal/delivery/  # HTTP router, DTO envelope, and Tauri CORS middleware
 │
 ├── docs/                    # Architecture specs, SDD plans, and designs
 ├── plan/                    # Hackathon competition guidelines & pitch decks
 └── .agents/skills/          # Specialized engineering skills for AI agents
```

---

## ⚖️ 3. Non-Negotiable Hackathon Constraints (Strict!)

### 🛑 Constraint 1: Non-Advisory Compliance (Anti-Pelanggaran OJK)
- **STRICTLY FORBIDDEN**: Never output direct investment recommendations like `BUY`, `SELL`, `HOLD`, or `"Koleksi saham ini"`.
- **ALLOWED**: Output objective market signatures and indicators:
  - Direction: `Bullish`, `Bearish`, `Neutral`
  - Scores: `Opportunity Score` (0-100), `Risk Level` (`Low`, `Medium`, `High`)
  - Divergence: `Fundamental Divergence Detected (True/False)`
  - Anomaly: `Anomaly Flag (True/False)`, `Anomaly Score`
- **Mandatory Disclaimer**: Every user-facing intelligence summary MUST include:
  > *"Informasi dan analisis ini merupakan hasil pemrosesan data riset dan bukan merupakan anjuran investasi personal (Bukan rekomendasi Beli/Jual)."*

### ⚡ Constraint 2: Zero-Quota-Wasted Strategy
- Sectors API has a strict hard limit of **1,000 API credits per team**.
- All layers implement caching:
  - `data_processing` caches Sectors responses.
  - `ai_engine` has an in-memory cache with 1-hour TTL.
  - `backend` has a snapshot cache with 24-hour TTL (`CACHE_TTL_HOURS=24`).
- Repeated requests for the same ticker must be served from cache in `<5ms` without making external API calls.

### 🔍 Constraint 3: Explainable AI (XAI) & Anti-Halusinasi
- The system computes facts first, AI explains second (*"Sistem menghitung, AI menjelaskan"*).
- Every score must trace back to numerical evidence (`EvidenceItem`, `relative_positions`, `significant_changes`).
- LLM temperature is capped at `0.2` with prompt instructions forbidding hallucinated numbers.

---

## 🛠️ 4. Quick Execution Runbook

### Running the Python AI Engine:
```powershell
cd ai_engine
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Test suite:
```powershell
python test_ai_engine.py
```

### Running the Go Backend:
```powershell
cd backend
go run ./cmd/api
```
*(Automatically falls back to In-Memory repository if local PostgreSQL is not running).*

Test suite:
```powershell
cd backend
go test -v ./tests/...
```

---

## 📜 5. Git Commit Standards
Follow **Conventional Commits**:
- `feat(scope): imperative description`
- `fix(scope): fix erroneous behavior`
- `refactor(scope): internal structural improvement`
- `test(scope): add or correct tests`
- `docs(scope): documentation only changes`
