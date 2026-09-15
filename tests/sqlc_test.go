package tests

import (
	"testing"
	"time"

	"be/db/sqlc"

	"github.com/jackc/pgx/v5/pgtype"
)

func TestSQLCQuerierInterface(t *testing.T) {
	// Verify that *sqlc.Queries implements sqlc.Querier
	var _ sqlc.Querier = (*sqlc.Queries)(nil)

	queries := sqlc.New(nil)
	if queries == nil {
		t.Fatal("expected queries instance not to be nil")
	}
}

func TestSQLCModelInstantiations(t *testing.T) {
	now := time.Now()
	var nowTz pgtype.Timestamptz
	_ = nowTz.Scan(now)

	// Test Company model
	comp := sqlc.Company{
		Symbol: "BBCA",
		Name:   "Bank Central Asia Tbk",
		Sector: "Financials",
		SubSector: pgtype.Text{
			String: "Banks",
			Valid:  true,
		},
		MarketCap: pgtype.Int8{
			Int64: 1000000000000,
			Valid: true,
		},
		CreatedAt: nowTz,
		UpdatedAt: nowTz,
	}
	if comp.Symbol != "BBCA" {
		t.Errorf("expected symbol BBCA, got %s", comp.Symbol)
	}

	// Test IntelligenceSnapshot model
	intel := sqlc.IntelligenceSnapshot{
		ID:                 1,
		Symbol:             "BBCA",
		Direction:          "Bullish",
		Confidence:         "High",
		RiskLevel:          "Low",
		IsAnomaly:          false,
		DivergenceDetected: true,
		PositiveFactors:    []byte(`["growth outperforming"]`),
		NegativeFactors:    []byte(`["low dividend"]`),
		SupportingFactors:  []byte(`["valuation compressed"]`),
		Evidence:           []byte(`[{"metric":"Growth"}]`),
		AiResearchSummary:  pgtype.Text{String: "Solid growth", Valid: true},
		ModelVersion:       "v3-stacking-rf",
		CreatedAt:          nowTz,
	}
	if intel.Symbol != "BBCA" || intel.Direction != "Bullish" {
		t.Errorf("unexpected intelligence snapshot fields: %+v", intel)
	}

	// Test SectorsDataSnapshot model
	snapshot := sqlc.SectorsDataSnapshot{
		ID:                1,
		Symbol:            "BBCA",
		ValuationMetrics:  []byte(`{"pe": 15.2}`),
		Financials:        []byte(`{"revenue": 100}`),
		InstitutionalFlow: []byte(`{"foreign_buy": 50}`),
		RawPayload:        []byte(`{}`),
		FetchedAt:         nowTz,
	}
	if snapshot.Symbol != "BBCA" {
		t.Errorf("expected symbol BBCA, got %s", snapshot.Symbol)
	}
}
