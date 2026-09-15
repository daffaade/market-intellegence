---
name: golang-clean-arch
description: Use when designing, creating, or refactoring Go backend services, packages, domain models, usecases, repositories, and HTTP/gRPC handlers to enforce Clean Architecture boundaries
---

# Golang Clean Architecture

## Overview
Enforce strict separation of concerns and dependency inversion in Go backend applications. The core domain logic must remain independent of frameworks, databases, external APIs, and transport layers.

```
       +---------------------------------------------+
       | Delivery Layer (HTTP / gRPC / CLI / Workers) |
       +---------------------------------------------+
                              | calls
                              v
       +---------------------------------------------+
       |       Usecase / Service Layer (App Logic)   |
       +---------------------------------------------+
           | calls (via interface)         ^ returns
           v                               |
       +---------------------------------------------+
       | Domain Layer (Entities, Errors, Interfaces) |
       +---------------------------------------------+
                              ^ implemented by
                              |
       +---------------------------------------------+
       | Repository / Adapter Layer (pgx, redis, API)|
       +---------------------------------------------+
```

---

## The Golden Rules of Dependency

1. **Inward Dependency Only**: Outer layers know about inner layers; inner layers NEVER import outer layers.
2. **Domain Purity**: `internal/domain` (or entity package) contains zero third-party dependencies (no database drivers, no web frameworks). Only standard library (e.g. `time`, `errors`) and domain structs/interfaces.
3. **Accept Interfaces, Return Structs**: Define consumer interfaces in the layer that needs them (usecase defines repository interface).
4. **No Circular Imports**: If package A imports package B, package B must never import package A. Interfaces break the cycle.

---

## Directory Layout Standards

```text
├── cmd/
│   └── api/
│       └── main.go               # Dependency injection wire-up & server startup
├── internal/
│   ├── domain/                   # Core business entities & repository interfaces
│   │   ├── stock.go
│   │   ├── signal.go
│   │   └── errors.go             # Sentinel domain errors (ErrNotFound, ErrUnauthorized)
│   ├── usecase/                  # Application business rules orchestrating domain & repos
│   │   ├── stock_usecase.go
│   │   └── signal_usecase.go
│   ├── repository/               # Data persistence implementations (sqlc/pgx, redis)
│   │   ├── postgres/
│   │   │   └── stock_repo.go
│   │   └── cache/
│   │       └── redis_cache.go
│   ├── delivery/                 # Transport adapters
│   │   └── http/
│   │       ├── router.go
│   │       ├── handler/
│   │       │   └── stock_handler.go
│   │       ├── middleware/
│   │       └── dto/              # Request/Response validation models
│   └── platform/                 # Infrastructure helpers (logger, config, telemetry)
```

---

## Layer Guidelines & Code Patterns

### 1. Domain Layer (`internal/domain`)
- Defines pure structs, value objects, and business rules.
- Declares repository/client interfaces needed by usecases.
- Declares domain-specific sentinel errors.

```go
package domain

import (
	"context"
	"errors"
	"time"
)

var (
	ErrStockNotFound   = errors.New("stock not found")
	ErrInvalidSymbol   = errors.New("invalid stock symbol")
	ErrInsufficientData = errors.New("insufficient historical data for signal")
)

type Stock struct {
	Symbol      string
	CompanyName string
	Sector      string
	MarketCap   int64
	UpdatedAt   time.Time
}

type StockRepository interface {
	GetBySymbol(ctx context.Context, symbol string) (*Stock, error)
	ListBySector(ctx context.Context, sector string, limit int, offset int) ([]Stock, error)
	Upsert(ctx context.Context, stock *Stock) error
}
```

### 2. Usecase / Service Layer (`internal/usecase`)
- Implements business use cases.
- Orchestrates multiple repositories, caches, or intelligence engines.
- NEVER handles HTTP/gRPC specifics (no `http.ResponseWriter`, `fiber.Ctx`, or status codes).

```go
package usecase

import (
	"context"
	"fmt"

	"be/internal/domain"
)

type StockUsecase interface {
	GetStockProfile(ctx context.Context, symbol string) (*domain.Stock, error)
}

type stockUsecase struct {
	repo  domain.StockRepository
	cache domain.CacheRepository
}

func NewStockUsecase(repo domain.StockRepository, cache domain.CacheRepository) StockUsecase {
	return &stockUsecase{
		repo:  repo,
		cache: cache,
	}
}

func (u *stockUsecase) GetStockProfile(ctx context.Context, symbol string) (*domain.Stock, error) {
	if symbol == "" {
		return nil, domain.ErrInvalidSymbol
	}

	stock, err := u.repo.GetBySymbol(ctx, symbol)
	if err != nil {
		return nil, fmt.Errorf("usecase.GetStockProfile: %w", err)
	}
	return stock, nil
}
```

### 3. Repository Layer (`internal/repository/postgres`)
- Implements `domain.StockRepository` using database queries (e.g. `sqlc` / `pgx`).
- Translates database-specific errors into domain errors.

```go
package postgres

import (
	"context"
	"errors"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"be/internal/domain"
)

type stockRepo struct {
	db *pgxpool.Pool
}

func NewStockRepository(db *pgxpool.Pool) domain.StockRepository {
	return &stockRepo{db: db}
}

func (r *stockRepo) GetBySymbol(ctx context.Context, symbol string) (*domain.Stock, error) {
	const query = `SELECT symbol, company_name, sector, market_cap, updated_at FROM stocks WHERE symbol = $1`
	var s domain.Stock
	err := r.db.QueryRow(ctx, query, symbol).Scan(&s.Symbol, &s.CompanyName, &s.Sector, &s.MarketCap, &s.UpdatedAt)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, domain.ErrStockNotFound
		}
		return nil, err
	}
	return &s, nil
}
```

### 4. Delivery Layer (`internal/delivery/http`)
- Parses request payloads into DTOs, validates input, calls Usecase, maps domain errors to HTTP status codes.

```go
func (h *StockHandler) GetStock(w http.ResponseWriter, r *http.Request) {
	symbol := r.PathValue("symbol")
	stock, err := h.usecase.GetStockProfile(r.Context(), symbol)
	if err != nil {
		if errors.Is(err, domain.ErrStockNotFound) {
			http.Error(w, "Stock not found", http.StatusNotFound)
			return
		}
		if errors.Is(err, domain.ErrInvalidSymbol) {
			http.Error(w, "Invalid symbol", http.StatusBadRequest)
			return
		}
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	renderJSON(w, http.StatusOK, ToStockResponse(stock))
}
```

---

## Anti-Patterns & Common Violations

| Violation | Problem | Correct Pattern |
|---|---|---|
| Domain importing `net/http` or `fiber` | Domain polluted with framework dependencies | Keep domain pure Go structs and interfaces |
| Handler executing SQL queries directly | Bypasses business validation and domain rules | Handler calls Usecase, Usecase calls Repository |
| Returning DB model directly to HTTP client | Leaks internal database schema and secrets | Map Domain model to Delivery DTO before response |
| Repository defining business logic | Mixes persistence with domain rules | Keep repo limited to CRUD and persistence semantics |
| Hardcoding concrete structs in usecases | Breaks unit testability and modularity | Inject interfaces into usecase constructors |

---

## Verification Checklist
- [ ] Run `go vet ./...` to verify package sanity.
- [ ] Ensure `internal/domain` has zero imports of `internal/delivery` or external DB drivers.
- [ ] Check that domain errors are properly wrapped with `%w` for `errors.Is` comparison.
- [ ] Verify `cmd/api/main.go` acts solely as the composition root (wiring dependencies).
