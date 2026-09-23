package tests

import (
	"context"
	"testing"
	"time"

	"be/internal/domain"
)

func TestDomainStructures(t *testing.T) {
	now := time.Now()

	comp := domain.Company{
		Symbol:    "BBCA",
		Name:      "Bank Central Asia Tbk",
		Sector:    "Financials",
		SubSector: "Banking",
		MarketCap: 1200000000000,
		UpdatedAt: now,
	}
	if comp.Symbol != "BBCA" || comp.MarketCap <= 0 {
		t.Errorf("company struct mismatch: %+v", comp)
	}

	fin := domain.FinancialSnapshot{
		Symbol:       "BBCA",
		SnapshotDate: now,
		ValuationMetrics: map[string]interface{}{
			"pe_ratio": 15.5,
		},
		Financials: map[string]interface{}{
			"revenue_growth": 0.12,
		},
		InstitutionalFlow: map[string]interface{}{
			"foreign_flow": 50000000000,
		},
		RawPayload: map[string]interface{}{
			"raw": true,
		},
		FetchedAt: now,
	}
	if fin.Symbol != "BBCA" || fin.ValuationMetrics["pe_ratio"] != 15.5 {
		t.Errorf("financial snapshot mismatch: %+v", fin)
	}

	snap := domain.IntelligenceSnapshot{
		ID:                 1,
		Symbol:             "BBCA",
		OpportunityScore:   84.5,
		RiskScore:          25.0,
		Direction:          "Bullish",
		Confidence:         "High",
		RiskLevel:          "Low",
		IsAnomaly:          true,
		AnomalyScore:       12.0,
		DivergenceDetected: true,
		PositiveFactors:    []string{"Growth 18% outperforming peer median 9%"},
		NegativeFactors:    []string{"Dividend yield slightly lower"},
		SupportingFactors:  []string{"Valuation compressed while growth forecast improved"},
		Evidence: []domain.EvidenceItem{
			{
				Metric:       "Growth",
				CompanyValue: "18%",
				PeerMedian:   "9%",
				Position:     "Outperform",
			},
		},
		WhatChanged: []domain.WhatChangedItem{
			{
				Metric:   "PE Ratio",
				Previous: "16x",
				Current:  "11x",
				Delta:    "-5x",
				Impact:   "Valuation compressed",
			},
		},
		PeerComparison: []domain.PeerComparisonItem{
			{
				Metric:     "PE Ratio",
				Target:     "11x",
				PeerMedian: "16x",
				Position:   "Cheaper",
			},
		},
		AIResearchSummary: "Deterministic synthesis shows strong fundamental tailwinds.",
		Disclaimer:        "Bukan rekomendasi Beli/Jual.",
		IsCached:           false,
		CreatedAt:          now,
	}
	if snap.Symbol != "BBCA" || snap.OpportunityScore != 84.5 || snap.Direction != "Bullish" {
		t.Errorf("domain struct mismatch: %+v", snap)
	}
	if len(snap.Evidence) != 1 || snap.Evidence[0].Metric != "Growth" {
		t.Errorf("evidence mismatch: %+v", snap.Evidence)
	}
	if len(snap.WhatChanged) != 1 || snap.WhatChanged[0].Metric != "PE Ratio" {
		t.Errorf("what_changed mismatch: %+v", snap.WhatChanged)
	}
	if len(snap.PeerComparison) != 1 || snap.PeerComparison[0].Position != "Cheaper" {
		t.Errorf("peer_comparison mismatch: %+v", snap.PeerComparison)
	}

	aiSumm := domain.AISummary{
		Symbol:     "BBCA",
		Summary:    "Analysis summary",
		Highlights: []string{"High growth"},
		Disclaimer: "Disclaimer note",
	}
	if aiSumm.Symbol != "BBCA" || aiSumm.Summary != "Analysis summary" {
		t.Errorf("ai summary mismatch: %+v", aiSumm)
	}
}

func TestDomainErrors(t *testing.T) {
	errs := []error{
		domain.ErrCompanyNotFound,
		domain.ErrInvalidSymbol,
		domain.ErrUpstreamTimeout,
		domain.ErrQuotaExceeded,
		domain.ErrIntelligenceFailed,
	}

	for _, err := range errs {
		if err == nil {
			t.Errorf("expected sentinel error to be non-nil")
		}
		if err.Error() == "" {
			t.Errorf("expected error message to be non-empty")
		}
	}
}

// Mock structs to test interface compatibility at compile time
type mockCompanyRepo struct{}

func (m *mockCompanyRepo) GetBySymbol(ctx context.Context, symbol string) (*domain.Company, error) {
	return &domain.Company{Symbol: symbol}, nil
}
func (m *mockCompanyRepo) ListAll(ctx context.Context) ([]domain.Company, error) {
	return []domain.Company{}, nil
}
func (m *mockCompanyRepo) ListBySector(ctx context.Context, sector string) ([]domain.Company, error) {
	return []domain.Company{}, nil
}
func (m *mockCompanyRepo) Upsert(ctx context.Context, comp *domain.Company) error {
	return nil
}

type mockSnapshotRepo struct{}

func (m *mockSnapshotRepo) GetLatestIntelligence(ctx context.Context, symbol string) (*domain.IntelligenceSnapshot, error) {
	return &domain.IntelligenceSnapshot{Symbol: symbol}, nil
}
func (m *mockSnapshotRepo) SaveIntelligence(ctx context.Context, snap *domain.IntelligenceSnapshot) error {
	return nil
}
func (m *mockSnapshotRepo) GetLatestSectorsData(ctx context.Context, symbol string) (*domain.FinancialSnapshot, error) {
	return &domain.FinancialSnapshot{Symbol: symbol}, nil
}
func (m *mockSnapshotRepo) SaveSectorsData(ctx context.Context, snap *domain.FinancialSnapshot) error {
	return nil
}
func (m *mockSnapshotRepo) GetTopOpportunities(ctx context.Context, limit int) ([]domain.IntelligenceSnapshot, error) {
	return []domain.IntelligenceSnapshot{}, nil
}
func (m *mockSnapshotRepo) GetTopRisks(ctx context.Context, limit int) ([]domain.IntelligenceSnapshot, error) {
	return []domain.IntelligenceSnapshot{}, nil
}
func (m *mockSnapshotRepo) GetRecentAnomalies(ctx context.Context, limit int) ([]domain.IntelligenceSnapshot, error) {
	return []domain.IntelligenceSnapshot{}, nil
}

type mockIntelligenceEngineClient struct{}

func (m *mockIntelligenceEngineClient) Analyze(ctx context.Context, req domain.AnalyzeRequest) (*domain.IntelligenceSnapshot, error) {
	return &domain.IntelligenceSnapshot{Symbol: req.Symbol}, nil
}

type mockAIExplanationClient struct{}

func (m *mockAIExplanationClient) GenerateSummary(ctx context.Context, snapshot *domain.IntelligenceSnapshot) (string, error) {
	return "Mock summary for " + snapshot.Symbol, nil
}

func TestDomainInterfaces(t *testing.T) {
	var _ domain.CompanyRepository = (*mockCompanyRepo)(nil)
	var _ domain.SnapshotRepository = (*mockSnapshotRepo)(nil)
	var _ domain.IntelligenceEngineClient = (*mockIntelligenceEngineClient)(nil)
	var _ domain.AIExplanationClient = (*mockAIExplanationClient)(nil)

	ctx := context.Background()
	compRepo := &mockCompanyRepo{}
	c, err := compRepo.GetBySymbol(ctx, "BBCA")
	if err != nil || c.Symbol != "BBCA" {
		t.Errorf("mockCompanyRepo failed")
	}

	snapRepo := &mockSnapshotRepo{}
	s, err := snapRepo.GetLatestIntelligence(ctx, "BBCA")
	if err != nil || s.Symbol != "BBCA" {
		t.Errorf("mockSnapshotRepo failed")
	}

	engine := &mockIntelligenceEngineClient{}
	engSnap, err := engine.Analyze(ctx, domain.AnalyzeRequest{Symbol: "BBCA"})
	if err != nil || engSnap.Symbol != "BBCA" {
		t.Errorf("mockIntelligenceEngineClient failed")
	}

	aiClient := &mockAIExplanationClient{}
	summary, err := aiClient.GenerateSummary(ctx, engSnap)
	if err != nil || summary != "Mock summary for BBCA" {
		t.Errorf("mockAIExplanationClient failed")
	}
}
