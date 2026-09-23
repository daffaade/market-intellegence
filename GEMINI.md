# GEMINI.md — Project Rules & Hackathon Context

See detailed guidelines, constraints, and architecture in [AGENTS.md](./AGENTS.md).

## Critical Context Summary:
1. **Competition**: Sectors Hackathon Indonesia 2026 — Track 03 (Market Intelligence).
2. **Regulatory Rule**: STRICTLY NON-ADVISORY (NO BUY/SELL/HOLD advice). Always attach mandatory legal disclaimer.
3. **Quota Rule**: Protect 1,000 Sectors API credit limit via multi-layer caching.
4. **Architecture**:
   - `data_processing/`: Sectors + YFinance data pipelines.
   - `ai_engine/`: FastAPI Python AI service on port 8000 (`POST /api/v1/analyze`).
   - `backend/`: Go Clean Architecture service on port 8080 (`go run ./cmd/api`).
5. **Specialized Skills**: Located in `.agents/skills/` (`git-commit-convention`, `go-concurrency-guard`, `golang-clean-arch`, `grillme`, `sqlc-pgx-expert`).
