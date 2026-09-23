package tests

import (
	"context"
	"encoding/json"
	"errors"
	"testing"
	"time"

	"be/db/sqlc"
	"be/internal/domain"
	"be/internal/repository/postgres"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
)

// mockQuerier implements sqlc.Querier for unit testing without live PostgreSQL.
type mockQuerier struct {
	getCompanyFn                 func(ctx context.Context, symbol string) (sqlc.Company, error)
	listCompaniesFn              func(ctx context.Context) ([]sqlc.Company, error)
	listCompaniesBySectorFn      func(ctx context.Context, sector string) ([]sqlc.Company, error)
	upsertCompanyFn              func(ctx context.Context, arg sqlc.UpsertCompanyParams) (sqlc.Company, error)
	getLatestIntelligenceFn      func(ctx context.Context, symbol string) (sqlc.IntelligenceSnapshot, error)
	insertIntelligenceSnapshotFn func(ctx context.Context, arg sqlc.InsertIntelligenceSnapshotParams) (sqlc.IntelligenceSnapshot, error)
	getLatestSectorsSnapshotFn   func(ctx context.Context, symbol string) (sqlc.SectorsDataSnapshot, error)
	getSectorsSnapshotByDateFn   func(ctx context.Context, arg sqlc.GetSectorsSnapshotByDateParams) (sqlc.SectorsDataSnapshot, error)
	upsertSectorsSnapshotFn      func(ctx context.Context, arg sqlc.UpsertSectorsSnapshotParams) (sqlc.SectorsDataSnapshot, error)
	getTopOpportunitiesFn        func(ctx context.Context, limit int32) ([]sqlc.IntelligenceSnapshot, error)
	getTopRisksFn                func(ctx context.Context, limit int32) ([]sqlc.IntelligenceSnapshot, error)
	getRecentAnomaliesFn         func(ctx context.Context, limit int32) ([]sqlc.IntelligenceSnapshot, error)
}

func (m *mockQuerier) GetCompany(ctx context.Context, symbol string) (sqlc.Company, error) {
	if m.getCompanyFn != nil {
		return m.getCompanyFn(ctx, symbol)
	}
	return sqlc.Company{}, errors.New("not implemented")
}

func (m *mockQuerier) ListCompanies(ctx context.Context) ([]sqlc.Company, error) {
	if m.listCompaniesFn != nil {
		return m.listCompaniesFn(ctx)
	}
	return nil, errors.New("not implemented")
}

func (m *mockQuerier) ListCompaniesBySector(ctx context.Context, sector string) ([]sqlc.Company, error) {
	if m.listCompaniesBySectorFn != nil {
		return m.listCompaniesBySectorFn(ctx, sector)
	}
	return nil, errors.New("not implemented")
}

func (m *mockQuerier) UpsertCompany(ctx context.Context, arg sqlc.UpsertCompanyParams) (sqlc.Company, error) {
	if m.upsertCompanyFn != nil {
		return m.upsertCompanyFn(ctx, arg)
	}
	return sqlc.Company{}, errors.New("not implemented")
}

func (m *mockQuerier) GetLatestIntelligence(ctx context.Context, symbol string) (sqlc.IntelligenceSnapshot, error) {
	if m.getLatestIntelligenceFn != nil {
		return m.getLatestIntelligenceFn(ctx, symbol)
	}
	return sqlc.IntelligenceSnapshot{}, errors.New("not implemented")
}

func (m *mockQuerier) InsertIntelligenceSnapshot(ctx context.Context, arg sqlc.InsertIntelligenceSnapshotParams) (sqlc.IntelligenceSnapshot, error) {
	if m.insertIntelligenceSnapshotFn != nil {
		return m.insertIntelligenceSnapshotFn(ctx, arg)
	}
	return sqlc.IntelligenceSnapshot{}, errors.New("not implemented")
}

func (m *mockQuerier) GetLatestSectorsSnapshot(ctx context.Context, symbol string) (sqlc.SectorsDataSnapshot, error) {
	if m.getLatestSectorsSnapshotFn != nil {
		return m.getLatestSectorsSnapshotFn(ctx, symbol)
	}
	return sqlc.SectorsDataSnapshot{}, errors.New("not implemented")
}

func (m *mockQuerier) GetSectorsSnapshotByDate(ctx context.Context, arg sqlc.GetSectorsSnapshotByDateParams) (sqlc.SectorsDataSnapshot, error) {
	if m.getSectorsSnapshotByDateFn != nil {
		return m.getSectorsSnapshotByDateFn(ctx, arg)
	}
	return sqlc.SectorsDataSnapshot{}, errors.New("not implemented")
}

func (m *mockQuerier) UpsertSectorsSnapshot(ctx context.Context, arg sqlc.UpsertSectorsSnapshotParams) (sqlc.SectorsDataSnapshot, error) {
	if m.upsertSectorsSnapshotFn != nil {
		return m.upsertSectorsSnapshotFn(ctx, arg)
	}
	return sqlc.SectorsDataSnapshot{}, errors.New("not implemented")
}

func (m *mockQuerier) GetTopOpportunities(ctx context.Context, limit int32) ([]sqlc.IntelligenceSnapshot, error) {
	if m.getTopOpportunitiesFn != nil {
		return m.getTopOpportunitiesFn(ctx, limit)
	}
	return nil, errors.New("not implemented")
}

func (m *mockQuerier) GetTopRisks(ctx context.Context, limit int32) ([]sqlc.IntelligenceSnapshot, error) {
	if m.getTopRisksFn != nil {
		return m.getTopRisksFn(ctx, limit)
	}
	return nil, errors.New("not implemented")
}

func (m *mockQuerier) GetRecentAnomalies(ctx context.Context, limit int32) ([]sqlc.IntelligenceSnapshot, error) {
	if m.getRecentAnomaliesFn != nil {
		return m.getRecentAnomaliesFn(ctx, limit)
	}
	return nil, errors.New("not implemented")
}

var _ sqlc.Querier = (*mockQuerier)(nil)

// 1. Connection Pool Tests
func TestPoolConfig(t *testing.T) {
	validDSN := "postgres://user:password@localhost:5432/testdb?sslmode=disable"
	cfg, err := postgres.NewPoolConfig(validDSN)
	if err != nil {
		t.Fatalf("unexpected error parsing pool config: %v", err)
	}

	if cfg.MaxConns != 25 {
		t.Errorf("expected MaxConns=25, got %d", cfg.MaxConns)
	}
	if cfg.MinConns != 5 {
		t.Errorf("expected MinConns=5, got %d", cfg.MinConns)
	}
	if cfg.MaxConnLifetime != 1*time.Hour {
		t.Errorf("expected MaxConnLifetime=1h, got %v", cfg.MaxConnLifetime)
	}
	if cfg.MaxConnIdleTime != 30*time.Minute {
		t.Errorf("expected MaxConnIdleTime=30m, got %v", cfg.MaxConnIdleTime)
	}

	// Invalid DSN
	_, err = postgres.NewPoolConfig("://invalid-url")
	if err == nil {
		t.Errorf("expected error for invalid DSN, got nil")
	}

	// NewPool with invalid DSN
	ctx := context.Background()
	_, err = postgres.NewPool(ctx, "://invalid-url")
	if err == nil {
		t.Errorf("expected NewPool error for invalid DSN, got nil")
	}
}

// 2. Interface Compliance Test
func TestRepositoryInterfaces(t *testing.T) {
	var _ domain.CompanyRepository = (*postgres.CompanyRepository)(nil)
	var _ domain.SnapshotRepository = (*postgres.SnapshotRepository)(nil)
}

// 3. Company Repository Tests
func TestCompanyRepository_GetBySymbol(t *testing.T) {
	ctx := context.Background()
	now := time.Now().Truncate(time.Second)

	t.Run("success mapping", func(t *testing.T) {
		mock := &mockQuerier{
			getCompanyFn: func(ctx context.Context, symbol string) (sqlc.Company, error) {
				if symbol != "BBCA" {
					return sqlc.Company{}, errors.New("unexpected symbol")
				}
				return sqlc.Company{
					Symbol:    "BBCA",
					Name:      "Bank Central Asia Tbk",
					Sector:    "Financials",
					SubSector: pgtype.Text{String: "Banking", Valid: true},
					MarketCap: pgtype.Int8{Int64: 1200000000000, Valid: true},
					UpdatedAt: pgtype.Timestamptz{Time: now, Valid: true},
				}, nil
			},
		}

		repo := postgres.NewCompanyRepository(mock)
		comp, err := repo.GetBySymbol(ctx, "BBCA")
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}

		if comp.Symbol != "BBCA" || comp.Name != "Bank Central Asia Tbk" {
			t.Errorf("mismatched company data: %+v", comp)
		}
		if comp.SubSector != "Banking" || comp.MarketCap != 1200000000000 {
			t.Errorf("mismatched optional fields: SubSector=%s, MarketCap=%d", comp.SubSector, comp.MarketCap)
		}
		if !comp.UpdatedAt.Equal(now) {
			t.Errorf("mismatched UpdatedAt: %v != %v", comp.UpdatedAt, now)
		}
	})

	t.Run("not found translation to domain.ErrCompanyNotFound", func(t *testing.T) {
		mock := &mockQuerier{
			getCompanyFn: func(ctx context.Context, symbol string) (sqlc.Company, error) {
				return sqlc.Company{}, pgx.ErrNoRows
			},
		}

		repo := postgres.NewCompanyRepository(mock)
		comp, err := repo.GetBySymbol(ctx, "UNKNOWN")
		if comp != nil {
			t.Errorf("expected nil company, got %+v", comp)
		}
		if !errors.Is(err, domain.ErrCompanyNotFound) {
			t.Errorf("expected ErrCompanyNotFound, got %v", err)
		}
	})

	t.Run("database error propagation", func(t *testing.T) {
		dbErr := errors.New("connection failed")
		mock := &mockQuerier{
			getCompanyFn: func(ctx context.Context, symbol string) (sqlc.Company, error) {
				return sqlc.Company{}, dbErr
			},
		}

		repo := postgres.NewCompanyRepository(mock)
		_, err := repo.GetBySymbol(ctx, "BBCA")
		if err == nil || !errors.Is(err, dbErr) {
			t.Errorf("expected wrapped db error, got %v", err)
		}
	})
}

func TestCompanyRepository_ListAll(t *testing.T) {
	ctx := context.Background()

	t.Run("success multiple companies", func(t *testing.T) {
		mock := &mockQuerier{
			listCompaniesFn: func(ctx context.Context) ([]sqlc.Company, error) {
				return []sqlc.Company{
					{Symbol: "BBCA", Name: "BCA", Sector: "Financials"},
					{Symbol: "TLKM", Name: "Telkom", Sector: "Infrastructure"},
				}, nil
			},
		}

		repo := postgres.NewCompanyRepository(mock)
		comps, err := repo.ListAll(ctx)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if len(comps) != 2 {
			t.Fatalf("expected 2 companies, got %d", len(comps))
		}
		if comps[0].Symbol != "BBCA" || comps[1].Symbol != "TLKM" {
			t.Errorf("unexpected company list order or contents: %+v", comps)
		}
	})

	t.Run("empty list", func(t *testing.T) {
		mock := &mockQuerier{
			listCompaniesFn: func(ctx context.Context) ([]sqlc.Company, error) {
				return []sqlc.Company{}, nil
			},
		}

		repo := postgres.NewCompanyRepository(mock)
		comps, err := repo.ListAll(ctx)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if len(comps) != 0 {
			t.Errorf("expected 0 companies, got %d", len(comps))
		}
	})

	t.Run("database error", func(t *testing.T) {
		mock := &mockQuerier{
			listCompaniesFn: func(ctx context.Context) ([]sqlc.Company, error) {
				return nil, errors.New("query timeout")
			},
		}

		repo := postgres.NewCompanyRepository(mock)
		_, err := repo.ListAll(ctx)
		if err == nil {
			t.Errorf("expected error, got nil")
		}
	})
}

func TestCompanyRepository_ListBySector(t *testing.T) {
	ctx := context.Background()

	t.Run("success filter by sector", func(t *testing.T) {
		mock := &mockQuerier{
			listCompaniesBySectorFn: func(ctx context.Context, sector string) ([]sqlc.Company, error) {
				if sector != "Financials" {
					return nil, errors.New("unexpected sector")
				}
				return []sqlc.Company{
					{Symbol: "BBCA", Sector: "Financials"},
					{Symbol: "BBRI", Sector: "Financials"},
				}, nil
			},
		}

		repo := postgres.NewCompanyRepository(mock)
		comps, err := repo.ListBySector(ctx, "Financials")
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if len(comps) != 2 {
			t.Fatalf("expected 2 companies, got %d", len(comps))
		}
	})

	t.Run("database error", func(t *testing.T) {
		mock := &mockQuerier{
			listCompaniesBySectorFn: func(ctx context.Context, sector string) ([]sqlc.Company, error) {
				return nil, errors.New("db error")
			},
		}

		repo := postgres.NewCompanyRepository(mock)
		_, err := repo.ListBySector(ctx, "Financials")
		if err == nil {
			t.Errorf("expected error, got nil")
		}
	})
}

func TestCompanyRepository_Upsert(t *testing.T) {
	ctx := context.Background()
	now := time.Now().Truncate(time.Second)

	t.Run("nil company error", func(t *testing.T) {
		repo := postgres.NewCompanyRepository(&mockQuerier{})
		err := repo.Upsert(ctx, nil)
		if err == nil {
			t.Errorf("expected error for nil company, got nil")
		}
	})

	t.Run("success upsert", func(t *testing.T) {
		mock := &mockQuerier{
			upsertCompanyFn: func(ctx context.Context, arg sqlc.UpsertCompanyParams) (sqlc.Company, error) {
				if arg.Symbol != "BBCA" || arg.Name != "BCA" {
					return sqlc.Company{}, errors.New("invalid arguments")
				}
				return sqlc.Company{
					Symbol:    arg.Symbol,
					Name:      arg.Name,
					Sector:    arg.Sector,
					SubSector: arg.SubSector,
					MarketCap: arg.MarketCap,
					UpdatedAt: pgtype.Timestamptz{Time: now, Valid: true},
				}, nil
			},
		}

		repo := postgres.NewCompanyRepository(mock)
		comp := &domain.Company{
			Symbol:    "BBCA",
			Name:      "BCA",
			Sector:    "Financials",
			SubSector: "Banking",
			MarketCap: 1200000000000,
		}

		err := repo.Upsert(ctx, comp)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if !comp.UpdatedAt.Equal(now) {
			t.Errorf("expected comp.UpdatedAt to be populated from DB, got %v", comp.UpdatedAt)
		}
	})

	t.Run("database error", func(t *testing.T) {
		mock := &mockQuerier{
			upsertCompanyFn: func(ctx context.Context, arg sqlc.UpsertCompanyParams) (sqlc.Company, error) {
				return sqlc.Company{}, errors.New("insert conflict error")
			},
		}

		repo := postgres.NewCompanyRepository(mock)
		comp := &domain.Company{Symbol: "BBCA"}
		err := repo.Upsert(ctx, comp)
		if err == nil {
			t.Errorf("expected error, got nil")
		}
	})
}

// 4. Snapshot Repository Tests
func TestSnapshotRepository_GetLatestIntelligence(t *testing.T) {
	ctx := context.Background()
	now := time.Now().Truncate(time.Second)

	posFactors, _ := json.Marshal([]string{"Strong ROE", "PE Compressed"})
	negFactors, _ := json.Marshal([]string{"Yield Down"})
	supFactors, _ := json.Marshal([]string{"Sector outperformance"})
	evidence, _ := json.Marshal([]domain.EvidenceItem{
		{Metric: "ROE", CompanyValue: "20%", PeerMedian: "12%", Position: "Outperform"},
	})

	var oppScore pgtype.Numeric
	_ = oppScore.Scan("84.50")
	var riskScore pgtype.Numeric
	_ = riskScore.Scan("25.00")
	var anomalyScore pgtype.Numeric
	_ = anomalyScore.Scan("12.50")

	t.Run("success mapping with JSONB deserialization", func(t *testing.T) {
		mock := &mockQuerier{
			getLatestIntelligenceFn: func(ctx context.Context, symbol string) (sqlc.IntelligenceSnapshot, error) {
				if symbol != "BBCA" {
					return sqlc.IntelligenceSnapshot{}, errors.New("unexpected symbol")
				}
				return sqlc.IntelligenceSnapshot{
					ID:                 42,
					Symbol:             "BBCA",
					OpportunityScore:   oppScore,
					RiskScore:          riskScore,
					Direction:          "Bullish",
					Confidence:         "High",
					RiskLevel:          "Low",
					IsAnomaly:          true,
					AnomalyScore:       anomalyScore,
					DivergenceDetected: true,
					PositiveFactors:    posFactors,
					NegativeFactors:    negFactors,
					SupportingFactors:  supFactors,
					Evidence:           evidence,
					AiResearchSummary:  pgtype.Text{String: "Promising outlook", Valid: true},
					ModelVersion:       "v3-stacking-rf",
					CreatedAt:          pgtype.Timestamptz{Time: now, Valid: true},
				}, nil
			},
		}

		repo := postgres.NewSnapshotRepository(mock)
		snap, err := repo.GetLatestIntelligence(ctx, "BBCA")
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}

		if snap.ID != 42 || snap.Symbol != "BBCA" {
			t.Errorf("mismatched id/symbol: %d/%s", snap.ID, snap.Symbol)
		}
		if snap.OpportunityScore != 84.5 || snap.RiskScore != 25.0 || snap.AnomalyScore != 12.5 {
			t.Errorf("numeric score conversion mismatch: Opp=%f, Risk=%f, Anomaly=%f", snap.OpportunityScore, snap.RiskScore, snap.AnomalyScore)
		}
		if len(snap.PositiveFactors) != 2 || snap.PositiveFactors[0] != "Strong ROE" {
			t.Errorf("positive factors mismatch: %+v", snap.PositiveFactors)
		}
		if len(snap.NegativeFactors) != 1 || snap.NegativeFactors[0] != "Yield Down" {
			t.Errorf("negative factors mismatch: %+v", snap.NegativeFactors)
		}
		if len(snap.SupportingFactors) != 1 || snap.SupportingFactors[0] != "Sector outperformance" {
			t.Errorf("supporting factors mismatch: %+v", snap.SupportingFactors)
		}
		if len(snap.Evidence) != 1 || snap.Evidence[0].Metric != "ROE" {
			t.Errorf("evidence mismatch: %+v", snap.Evidence)
		}
		if snap.AIResearchSummary != "Promising outlook" {
			t.Errorf("ai summary mismatch: %s", snap.AIResearchSummary)
		}
		if !snap.CreatedAt.Equal(now) {
			t.Errorf("created at mismatch: %v != %v", snap.CreatedAt, now)
		}
	})

	t.Run("empty/null JSONB fallback", func(t *testing.T) {
		mock := &mockQuerier{
			getLatestIntelligenceFn: func(ctx context.Context, symbol string) (sqlc.IntelligenceSnapshot, error) {
				return sqlc.IntelligenceSnapshot{
					ID:                1,
					Symbol:            "BBCA",
					PositiveFactors:   []byte("null"),
					NegativeFactors:   nil,
					SupportingFactors: []byte(""),
					Evidence:          []byte("null"),
				}, nil
			},
		}

		repo := postgres.NewSnapshotRepository(mock)
		snap, err := repo.GetLatestIntelligence(ctx, "BBCA")
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if snap.PositiveFactors == nil || len(snap.PositiveFactors) != 0 {
			t.Errorf("expected empty positive factors, got %+v", snap.PositiveFactors)
		}
		if snap.Evidence == nil || len(snap.Evidence) != 0 {
			t.Errorf("expected empty evidence, got %+v", snap.Evidence)
		}
	})

	t.Run("not found translation to domain.ErrCompanyNotFound", func(t *testing.T) {
		mock := &mockQuerier{
			getLatestIntelligenceFn: func(ctx context.Context, symbol string) (sqlc.IntelligenceSnapshot, error) {
				return sqlc.IntelligenceSnapshot{}, pgx.ErrNoRows
			},
		}

		repo := postgres.NewSnapshotRepository(mock)
		snap, err := repo.GetLatestIntelligence(ctx, "UNKNOWN")
		if snap != nil {
			t.Errorf("expected nil snapshot, got %+v", snap)
		}
		if !errors.Is(err, domain.ErrCompanyNotFound) {
			t.Errorf("expected ErrCompanyNotFound, got %v", err)
		}
	})

	t.Run("corrupted JSONB error handling", func(t *testing.T) {
		mock := &mockQuerier{
			getLatestIntelligenceFn: func(ctx context.Context, symbol string) (sqlc.IntelligenceSnapshot, error) {
				return sqlc.IntelligenceSnapshot{
					Symbol:          "BBCA",
					PositiveFactors: []byte("{invalid-json}"),
				}, nil
			},
		}

		repo := postgres.NewSnapshotRepository(mock)
		_, err := repo.GetLatestIntelligence(ctx, "BBCA")
		if err == nil {
			t.Errorf("expected JSON unmarshal error, got nil")
		}
	})
}

func TestSnapshotRepository_SaveIntelligence(t *testing.T) {
	ctx := context.Background()
	now := time.Now().Truncate(time.Second)

	t.Run("nil snapshot error", func(t *testing.T) {
		repo := postgres.NewSnapshotRepository(&mockQuerier{})
		err := repo.SaveIntelligence(ctx, nil)
		if err == nil {
			t.Errorf("expected error for nil snapshot, got nil")
		}
	})

	t.Run("success save with JSONB serialization", func(t *testing.T) {
		var capturedParams sqlc.InsertIntelligenceSnapshotParams
		mock := &mockQuerier{
			insertIntelligenceSnapshotFn: func(ctx context.Context, arg sqlc.InsertIntelligenceSnapshotParams) (sqlc.IntelligenceSnapshot, error) {
				capturedParams = arg
				return sqlc.IntelligenceSnapshot{
					ID:        99,
					Symbol:    arg.Symbol,
					CreatedAt: pgtype.Timestamptz{Time: now, Valid: true},
				}, nil
			},
		}

		repo := postgres.NewSnapshotRepository(mock)
		snap := &domain.IntelligenceSnapshot{
			Symbol:             "BBCA",
			OpportunityScore:   85.5,
			RiskScore:          20.0,
			Direction:          "Bullish",
			Confidence:         "High",
			RiskLevel:          "Low",
			IsAnomaly:          true,
			AnomalyScore:       10.0,
			DivergenceDetected: true,
			PositiveFactors:    []string{"P1", "P2"},
			NegativeFactors:    []string{"N1"},
			SupportingFactors:  []string{"S1"},
			Evidence: []domain.EvidenceItem{
				{Metric: "PE", CompanyValue: "11x", PeerMedian: "16x", Position: "Cheaper"},
			},
			AIResearchSummary: "Strong fundamental narrative.",
		}

		err := repo.SaveIntelligence(ctx, snap)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}

		if snap.ID != 99 {
			t.Errorf("expected snap.ID=99, got %d", snap.ID)
		}
		if !snap.CreatedAt.Equal(now) {
			t.Errorf("expected snap.CreatedAt=%v, got %v", now, snap.CreatedAt)
		}

		// Verify captured JSONB params
		var pos []string
		if err := json.Unmarshal(capturedParams.PositiveFactors, &pos); err != nil || len(pos) != 2 {
			t.Errorf("failed verifying positive factors JSONB: %v, %v", err, string(capturedParams.PositiveFactors))
		}
		var ev []domain.EvidenceItem
		if err := json.Unmarshal(capturedParams.Evidence, &ev); err != nil || len(ev) != 1 || ev[0].Metric != "PE" {
			t.Errorf("failed verifying evidence JSONB: %v, %v", err, string(capturedParams.Evidence))
		}
	})

	t.Run("database error propagation", func(t *testing.T) {
		mock := &mockQuerier{
			insertIntelligenceSnapshotFn: func(ctx context.Context, arg sqlc.InsertIntelligenceSnapshotParams) (sqlc.IntelligenceSnapshot, error) {
				return sqlc.IntelligenceSnapshot{}, errors.New("foreign key violation")
			},
		}

		repo := postgres.NewSnapshotRepository(mock)
		snap := &domain.IntelligenceSnapshot{Symbol: "UNKNOWN"}
		err := repo.SaveIntelligence(ctx, snap)
		if err == nil {
			t.Errorf("expected error, got nil")
		}
	})
}

func TestSnapshotRepository_GetLatestSectorsData(t *testing.T) {
	ctx := context.Background()
	now := time.Now().Truncate(time.Second)

	valMetrics, _ := json.Marshal(map[string]interface{}{"pe_ratio": 15.5})
	financials, _ := json.Marshal(map[string]interface{}{"revenue": 1000000000.0})
	instFlow, _ := json.Marshal(map[string]interface{}{"net_foreign": 50000.0})
	rawPayload, _ := json.Marshal(map[string]interface{}{"status": "ok"})

	t.Run("success mapping", func(t *testing.T) {
		mock := &mockQuerier{
			getLatestSectorsSnapshotFn: func(ctx context.Context, symbol string) (sqlc.SectorsDataSnapshot, error) {
				if symbol != "BBCA" {
					return sqlc.SectorsDataSnapshot{}, errors.New("unexpected symbol")
				}
				return sqlc.SectorsDataSnapshot{
					ID:                10,
					Symbol:            "BBCA",
					SnapshotDate:      pgtype.Date{Time: now, Valid: true},
					ValuationMetrics:  valMetrics,
					Financials:        financials,
					InstitutionalFlow: instFlow,
					RawPayload:        rawPayload,
					FetchedAt:         pgtype.Timestamptz{Time: now, Valid: true},
				}, nil
			},
		}

		repo := postgres.NewSnapshotRepository(mock)
		fin, err := repo.GetLatestSectorsData(ctx, "BBCA")
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}

		if fin.Symbol != "BBCA" {
			t.Errorf("expected symbol BBCA, got %s", fin.Symbol)
		}
		if fin.ValuationMetrics["pe_ratio"] != 15.5 {
			t.Errorf("valuation metrics mismatch: %+v", fin.ValuationMetrics)
		}
		if fin.Financials["revenue"] != 1000000000.0 {
			t.Errorf("financials mismatch: %+v", fin.Financials)
		}
	})

	t.Run("not found translation to domain.ErrCompanyNotFound", func(t *testing.T) {
		mock := &mockQuerier{
			getLatestSectorsSnapshotFn: func(ctx context.Context, symbol string) (sqlc.SectorsDataSnapshot, error) {
				return sqlc.SectorsDataSnapshot{}, pgx.ErrNoRows
			},
		}

		repo := postgres.NewSnapshotRepository(mock)
		fin, err := repo.GetLatestSectorsData(ctx, "UNKNOWN")
		if fin != nil {
			t.Errorf("expected nil snapshot, got %+v", fin)
		}
		if !errors.Is(err, domain.ErrCompanyNotFound) {
			t.Errorf("expected ErrCompanyNotFound, got %v", err)
		}
	})

	t.Run("corrupted JSONB handling", func(t *testing.T) {
		mock := &mockQuerier{
			getLatestSectorsSnapshotFn: func(ctx context.Context, symbol string) (sqlc.SectorsDataSnapshot, error) {
				return sqlc.SectorsDataSnapshot{
					Symbol:           "BBCA",
					ValuationMetrics: []byte("{corrupt}"),
				}, nil
			},
		}

		repo := postgres.NewSnapshotRepository(mock)
		_, err := repo.GetLatestSectorsData(ctx, "BBCA")
		if err == nil {
			t.Errorf("expected unmarshal error, got nil")
		}
	})
}

func TestSnapshotRepository_SaveSectorsData(t *testing.T) {
	ctx := context.Background()
	now := time.Now().Truncate(time.Second)

	t.Run("nil snapshot error", func(t *testing.T) {
		repo := postgres.NewSnapshotRepository(&mockQuerier{})
		err := repo.SaveSectorsData(ctx, nil)
		if err == nil {
			t.Errorf("expected error for nil snapshot, got nil")
		}
	})

	t.Run("success upsert", func(t *testing.T) {
		var capturedParams sqlc.UpsertSectorsSnapshotParams
		mock := &mockQuerier{
			upsertSectorsSnapshotFn: func(ctx context.Context, arg sqlc.UpsertSectorsSnapshotParams) (sqlc.SectorsDataSnapshot, error) {
				capturedParams = arg
				return sqlc.SectorsDataSnapshot{
					ID:        15,
					Symbol:    arg.Symbol,
					FetchedAt: pgtype.Timestamptz{Time: now, Valid: true},
				}, nil
			},
		}

		repo := postgres.NewSnapshotRepository(mock)
		fin := &domain.FinancialSnapshot{
			Symbol:            "BBCA",
			SnapshotDate:      now,
			ValuationMetrics:  map[string]interface{}{"pe": 15.0},
			Financials:        map[string]interface{}{"growth": 0.12},
			InstitutionalFlow: map[string]interface{}{"net": 1000},
			RawPayload:        map[string]interface{}{"ok": true},
		}

		err := repo.SaveSectorsData(ctx, fin)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}

		if !fin.FetchedAt.Equal(now) {
			t.Errorf("expected fin.FetchedAt to be populated, got %v", fin.FetchedAt)
		}
		if capturedParams.Symbol != "BBCA" {
			t.Errorf("captured symbol mismatch: %s", capturedParams.Symbol)
		}
	})

	t.Run("database error", func(t *testing.T) {
		mock := &mockQuerier{
			upsertSectorsSnapshotFn: func(ctx context.Context, arg sqlc.UpsertSectorsSnapshotParams) (sqlc.SectorsDataSnapshot, error) {
				return sqlc.SectorsDataSnapshot{}, errors.New("db write failed")
			},
		}

		repo := postgres.NewSnapshotRepository(mock)
		err := repo.SaveSectorsData(ctx, &domain.FinancialSnapshot{Symbol: "BBCA"})
		if err == nil {
			t.Errorf("expected error, got nil")
		}
	})
}

func TestSnapshotRepository_RankingsAndAnomalies(t *testing.T) {
	ctx := context.Background()

	var oppScore pgtype.Numeric
	_ = oppScore.Scan("92.00")
	var riskScore pgtype.Numeric
	_ = riskScore.Scan("88.00")

	sampleIntel := sqlc.IntelligenceSnapshot{
		ID:                 101,
		Symbol:             "BBCA",
		OpportunityScore:   oppScore,
		RiskScore:          riskScore,
		PositiveFactors:    []byte("[]"),
		NegativeFactors:    []byte("[]"),
		SupportingFactors:  []byte("[]"),
		Evidence:           []byte("[]"),
		IsAnomaly:          true,
		DivergenceDetected: true,
	}

	t.Run("GetTopOpportunities", func(t *testing.T) {
		mock := &mockQuerier{
			getTopOpportunitiesFn: func(ctx context.Context, limit int32) ([]sqlc.IntelligenceSnapshot, error) {
				if limit != 5 {
					return nil, errors.New("limit mismatch")
				}
				return []sqlc.IntelligenceSnapshot{sampleIntel}, nil
			},
		}

		repo := postgres.NewSnapshotRepository(mock)
		list, err := repo.GetTopOpportunities(ctx, 5)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if len(list) != 1 || list[0].Symbol != "BBCA" {
			t.Errorf("expected 1 snapshot for BBCA, got %+v", list)
		}
		if list[0].OpportunityScore != 92.0 {
			t.Errorf("expected score 92.0, got %f", list[0].OpportunityScore)
		}
	})

	t.Run("GetTopOpportunities error", func(t *testing.T) {
		mock := &mockQuerier{
			getTopOpportunitiesFn: func(ctx context.Context, limit int32) ([]sqlc.IntelligenceSnapshot, error) {
				return nil, errors.New("db error")
			},
		}
		repo := postgres.NewSnapshotRepository(mock)
		_, err := repo.GetTopOpportunities(ctx, 5)
		if err == nil {
			t.Errorf("expected error, got nil")
		}
	})

	t.Run("GetTopRisks", func(t *testing.T) {
		mock := &mockQuerier{
			getTopRisksFn: func(ctx context.Context, limit int32) ([]sqlc.IntelligenceSnapshot, error) {
				return []sqlc.IntelligenceSnapshot{sampleIntel}, nil
			},
		}

		repo := postgres.NewSnapshotRepository(mock)
		list, err := repo.GetTopRisks(ctx, 5)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if len(list) != 1 || list[0].RiskScore != 88.0 {
			t.Errorf("expected risk score 88.0, got %+v", list)
		}
	})

	t.Run("GetTopRisks error", func(t *testing.T) {
		mock := &mockQuerier{
			getTopRisksFn: func(ctx context.Context, limit int32) ([]sqlc.IntelligenceSnapshot, error) {
				return nil, errors.New("db error")
			},
		}
		repo := postgres.NewSnapshotRepository(mock)
		_, err := repo.GetTopRisks(ctx, 5)
		if err == nil {
			t.Errorf("expected error, got nil")
		}
	})

	t.Run("GetRecentAnomalies", func(t *testing.T) {
		mock := &mockQuerier{
			getRecentAnomaliesFn: func(ctx context.Context, limit int32) ([]sqlc.IntelligenceSnapshot, error) {
				return []sqlc.IntelligenceSnapshot{sampleIntel}, nil
			},
		}

		repo := postgres.NewSnapshotRepository(mock)
		list, err := repo.GetRecentAnomalies(ctx, 5)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if len(list) != 1 || !list[0].IsAnomaly || !list[0].DivergenceDetected {
			t.Errorf("expected anomaly & divergence snapshot, got %+v", list)
		}
	})

	t.Run("GetRecentAnomalies error", func(t *testing.T) {
		mock := &mockQuerier{
			getRecentAnomaliesFn: func(ctx context.Context, limit int32) ([]sqlc.IntelligenceSnapshot, error) {
				return nil, errors.New("db error")
			},
		}
		repo := postgres.NewSnapshotRepository(mock)
		_, err := repo.GetRecentAnomalies(ctx, 5)
		if err == nil {
			t.Errorf("expected error, got nil")
		}
	})
}
