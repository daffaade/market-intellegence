---
name: engine-feature-wiring
description: Use when adding a new intelligence feature end to end across the repo: a Python AI engine model and FastAPI router (ai_engine/), plus the Go backend domain, adapter with deterministic fallback, usecase, handler, route, and tests (backend/). Use it for any new endpoint that the Go backend proxies to the Python engine.
---

# Engine Feature Wiring (Python engine to Go backend)

## Overview
A feature in this platform crosses two services:

```
ai_engine/   models/<feature>/  ->  routers/<feature>.py  ->  main.py include_router
                                          ^ HTTP (port 8000)
backend/     domain -> adapter/python_engine/client.go (+ fallback) -> usecase -> handler -> router.go
                                          v HTTP (port 8080) to the frontend
```

Two rules shape every feature:
- **Explainable AI (Constraint 3).** The system computes exact numbers first, and the AI only explains them afterward. Every score has to trace back to evidence (`EvidenceItem`, `relative_positions`, `significant_changes`).
- **Zero-crash fallback (Constraint 3).** If the Python engine is offline or cold-starting, the Go adapter must return a deterministic heuristic result. The backend must never return a 500 because the engine is down.

For Go layering rules (domain has zero external imports, and so on), defer to the `golang-clean-arch` skill in `.agents/skills/`.

## Reference Implementation
Copy the pattern from **portfolio risk**, which is complete on both sides:
- Python: `ai_engine/models/portofolio_risk/portofolio_risk.py`, `ai_engine/routers/portfolio.py` (prefix `/api/v1/portfolio`, route `POST /risk`)
- Go: `backend/internal/domain/portfolio.go`, `backend/internal/adapter/python_engine/client.go` (`CalculatePortfolioRisk`, `fallbackPortfolioRiskReport`), `backend/internal/usecase/portfolio_usecase.go` (normalises weights to 1.0), `backend/internal/delivery/http/handler/portfolio_handler.go`
- Tests: `ai_engine/tests/test_portfolio_risk.py`, `backend/tests/portfolio_usecase_test.go`, `backend/tests/portfolio_consumer_api_test.go`

## Procedure

### A. Python engine
1. Put the math in `ai_engine/models/<feature>/`. It must be pure, with no HTTP and no I/O. Return plain numbers and evidence.
2. Add `ai_engine/routers/<feature>.py` with `APIRouter(prefix="/api/v1/<feature>", tags=[...])`. Keep the handler thin: validate, call the model, return.
3. Register it in `ai_engine/main.py` with `app.include_router(...)`. The file currently includes analyze, sector, portfolio, and consumer.
4. If the feature calls Sectors, use the cache. See the `sectors-quota-guard` skill.
5. Add `ai_engine/tests/test_<feature>.py`. Use plain pytest functions with the `sys.path` setup that the existing tests use.

### B. Go backend
1. **Domain** (`backend/internal/domain/<feature>.go`): request and report structs, with no external imports.
2. **Adapter** (`backend/internal/adapter/python_engine/client.go`): add a method that POSTs to the engine. On any error, timeout, or non-2xx status, return `fallbackXxx(req)`, a deterministic heuristic that is tagged as fallback. Do not return the error to the handler.
3. **Usecase** (`backend/internal/usecase/<feature>_usecase.go`): validate and normalise input, then call the adapter through its interface.
4. **Handler** (`backend/internal/delivery/http/handler/<feature>_handler.go`): decode, call the usecase, and write the envelope from `dto/response.go`.
5. **Route** (`backend/internal/delivery/http/router.go`): add `mux.HandleFunc("POST /api/v1/<feature>/...", ...)`, using Go 1.22+ method patterns. Put it in the right feature group, and gate it the same way the neighbouring routes are gated.
6. **Tests** in `backend/tests/`. Cover the engine-up path and the engine-down fallback path. The fallback test is the one that matters most.

### C. Verify
```bash
# Python engine
cd ~/market-intellegence/ai_engine
python3 -m pytest tests/test_<feature>.py -q

# Go backend
cd ~/market-intellegence/backend
go test -count=1 ./tests/...
```
Then confirm the fallback without the engine running: stop the engine, call the new Go route, and check for a 200 with a fallback-tagged body.

## Checklist before you finish
- [ ] Output has no BUY/SELL/HOLD wording, and includes the disclaimer if it is user-facing (see `idx-compliance-check`).
- [ ] Every number in the response can be traced to a field the model computed.
- [ ] Engine offline returns 200 with a fallback, not 500.
- [ ] No new direct Sectors HTTP calls.
- [ ] Both test suites pass.
