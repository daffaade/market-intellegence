---
name: stack-runbook
description: Use when starting, stopping, restarting, or testing the market-intellegence stack locally or on the VPS, including the Python AI engine (port 8000), the Go backend (port 8080), the SSH tunnel to the desktop frontend, port-in-use errors, and the test suites
---

# Stack Runbook (AI Engine + Go Backend)

## Overview
Two services run on the VPS. The desktop app (Tauri + React) runs on the laptop and reaches the backend through an SSH tunnel or a direct URL.

```
Laptop (Tauri app) --http://localhost:8080--> SSH tunnel --> VPS :8080 (Go backend)
                                                                 |
                                                                 v HTTP
                                                           VPS :8000 (Python AI engine)
```

## Start the services

### 1. Python AI engine (port 8000)
```bash
cd ~/market-intellegence/ai_engine
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Note: the handover runbook says `python3 -m vicorn`. That is a typo. The correct module is `uvicorn`.

Endpoints: `POST /api/v1/analyze`, `GET /api/v1/sector/{sector}`, `POST /api/v1/portfolio/risk`, `POST /api/v1/consumer-behavior/analyze`, `POST /api/v1/screener`, `POST /api/v1/summary`.

### 2. Go backend (port 8080)
```bash
cd ~/market-intellegence/backend
go run ./cmd/api
# or, after a build:
./bin/api
```
The backend falls back to in-memory storage when local PostgreSQL is not running, so it starts without a database.

Start the engine first. The backend still works without it, because it uses deterministic fallbacks, but then you get fallback results and not real engine output.

### 3. Laptop tunnel (run on the laptop)
```bash
ssh -L 8080:localhost:8080 user@vps
```
The frontend reads `VITE_API_BASE_URL`. Use `http://localhost:8080` through the tunnel, or the VPS URL directly.

## "bind: address already in use"
A previous backend is still holding the port. Clear it and start again:
```bash
fuser -k 8080/tcp || kill -9 $(lsof -t -i:8080)
```
For the engine, use port 8000 in the same way. Check first what owns the port, so you do not kill an unrelated process:
```bash
lsof -i :8080
```

## Tests

```bash
# Go backend. Requires Go 1.25+ (go.mod says 1.25.0).
# On this VPS Go 1.25.0 lives in ~/.local/go (no root available): export PATH=$HOME/.local/go/bin:$PATH
# If `go` reports "invalid go version '1.25.0'", the toolchain is too old: upgrade Go, don't edit go.mod.
cd ~/market-intellegence/backend
go version
go test -count=1 ./tests/...

# Python engine: pytest-style tests in ai_engine/tests/
# Use the venv at ~/.venvs/market-ai (system python has no pip; PEP 668 blocks global installs).
# Recreate it with: python3 -m venv --without-pip ~/.venvs/market-ai, bootstrap pip, then
# pip install -r ~/market-intellegence/ai_engine/requirements.txt
cd ~/market-intellegence/ai_engine
~/.venvs/market-ai/bin/python -m pytest tests -q

# Root-level engine suite (from AGENTS.md)
cd ~/market-intellegence
python3 test_ai_engine.py
```
If `pytest` is missing, install it into the same environment you run the engine in. Do not change the test code to get around a missing dependency.

## Environment
Copy `.env.example` to `.env` at the repo root and fill in the keys. Key variables: `SECTORS_API_KEY`, `MOCK_SECTORS` (set `true` for tests and local work to save credits), `PYTHON_ENGINE_URL` (`http://localhost:8000`), `AI_PROVIDER` (`gemini`, `groq`, or `mock`), `PORT` (`8080`), `CACHE_TTL_HOURS` (`24`), `DATABASE_URL` (Postgres/Supabase connection string). Never print or commit real keys, and never dump `.env` with a plain `cat`; use `grep -o '^VAR='` or mask the value before showing it.

**`.env` location gotcha:** `backend/internal/platform/config/config.go` calls `godotenv.Load()` with no path, so it only finds `.env` in the process's current working directory. The repo's own `.env.example` lives at the repo root, and the runbook says `cd backend && go run ./cmd/api`, so a root-level `.env` is invisible to the backend unless you fix this. This repo's `backend/.env` is a symlink to `../.env` — keep it that way (don't replace it with a real file, don't delete it) so there is still one `.env` to edit. If `go run ./cmd/api` logs a Postgres connection error that mentions `localhost` or the literal default database name even though `DATABASE_URL` is set correctly, check `ls -la backend/.env` first before touching the connection string.

**PostgreSQL client on this VPS:** there's no `sudo`, so `psql` was installed by downloading the Debian `.deb` with `apt-get download` (no root needed) and extracting with `dpkg-deb -x` into `~/.local/pgclient`, with a thin wrapper at `~/.local/bin/psql` that sets `LD_LIBRARY_PATH` and execs the real binary at `~/.local/pgclient/usr/lib/postgresql/15/bin/psql`. It's already on `PATH`. Running bare `psql` with no connection string tries a local Unix socket and fails — that's expected, since there is no local Postgres server. Always pass a full connection string (Neon, Supabase, or whatever `DATABASE_URL` holds): `psql "$DATABASE_URL"`.

## Troubleshooting order
1. Engine up? `curl -s localhost:8000/docs` should return HTML. If not, check the uvicorn log for an import error. A missing `pytrends` shows as a guarded import, which is expected, and the server should not crash because of it.
2. Backend up? `curl -s localhost:8080/api/v1/health`.
3. Tunnel up? Run the health check from the laptop against `localhost:8080`.
4. Only then look at the code.
