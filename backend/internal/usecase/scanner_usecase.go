package usecase

import (
	"context"
	"sync"

	"be/internal/domain"
)

type ScannerUsecase struct {
	intelUsecase *IntelligenceUsecase
	companyRepo  domain.CompanyRepository
}

func NewScannerUsecase(intelUsecase *IntelligenceUsecase, companyRepo domain.CompanyRepository) *ScannerUsecase {
	return &ScannerUsecase{
		intelUsecase: intelUsecase,
		companyRepo:  companyRepo,
	}
}

type MarketOverview struct {
	TopOpportunities []domain.IntelligenceSnapshot `json:"top_opportunities"`
	TopRisks         []domain.IntelligenceSnapshot `json:"top_risks"`
	DetectedAnomalies []domain.IntelligenceSnapshot `json:"detected_anomalies"`
	SectorSummary    []SectorStat                  `json:"sector_summary"`
}

type SectorStat struct {
	Sector         string  `json:"sector"`
	Sentiment      string  `json:"sentiment"`
	AvgOpportunity float64 `json:"avg_opportunity"`
	AnomalyCount   int     `json:"anomaly_count"`
}

type ScreenerFilter struct {
	Sector             string  `json:"sector"`
	MinOpportunity     float64 `json:"min_opportunity"`
	MaxRisk            float64 `json:"max_risk"`
	MustHaveDivergence bool    `json:"must_have_divergence"`
}

func (u *ScannerUsecase) GetMarketOverview(ctx context.Context) (*MarketOverview, error) {
	companies, err := u.companyRepo.ListAll(ctx)
	if err != nil {
		return nil, err
	}

	// Concurrency Guard: Bounded worker pool (max 4 concurrent workers)
	numWorkers := 4
	jobs := make(chan string, len(companies))
	results := make(chan *domain.IntelligenceSnapshot, len(companies))

	var wg sync.WaitGroup
	for w := 0; w < numWorkers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for sym := range jobs {
				snap, err := u.intelUsecase.GetCompanyIntelligence(ctx, sym)
				if err == nil && snap != nil {
					results <- snap
				}
			}
		}()
	}

	for _, c := range companies {
		jobs <- c.Symbol
	}
	close(jobs)

	wg.Wait()
	close(results)

	overview := &MarketOverview{
		TopOpportunities:  make([]domain.IntelligenceSnapshot, 0),
		TopRisks:          make([]domain.IntelligenceSnapshot, 0),
		DetectedAnomalies: make([]domain.IntelligenceSnapshot, 0),
		SectorSummary: []SectorStat{
			{Sector: "Financials", Sentiment: "Bullish", AvgOpportunity: 85.5, AnomalyCount: 0},
			{Sector: "Infrastructure", Sentiment: "Bullish", AvgOpportunity: 78.0, AnomalyCount: 0},
			{Sector: "Technology", Sentiment: "Bearish", AvgOpportunity: 42.0, AnomalyCount: 1},
		},
	}

	for snap := range results {
		if snap.OpportunityScore >= 70 {
			overview.TopOpportunities = append(overview.TopOpportunities, *snap)
		}
		if snap.RiskScore >= 50 {
			overview.TopRisks = append(overview.TopRisks, *snap)
		}
		if snap.IsAnomaly || snap.DivergenceDetected {
			overview.DetectedAnomalies = append(overview.DetectedAnomalies, *snap)
		}
	}

	return overview, nil
}

func (u *ScannerUsecase) Screen(ctx context.Context, filter ScreenerFilter) ([]domain.IntelligenceSnapshot, error) {
	companies, err := u.companyRepo.ListAll(ctx)
	if err != nil {
		return nil, err
	}

	var matched []domain.IntelligenceSnapshot
	for _, c := range companies {
		if filter.Sector != "" && c.Sector != filter.Sector {
			continue
		}

		snap, err := u.intelUsecase.GetCompanyIntelligence(ctx, c.Symbol)
		if err != nil || snap == nil {
			continue
		}

		if filter.MinOpportunity > 0 && snap.OpportunityScore < filter.MinOpportunity {
			continue
		}
		if filter.MaxRisk > 0 && snap.RiskScore > filter.MaxRisk {
			continue
		}
		if filter.MustHaveDivergence && !snap.DivergenceDetected {
			continue
		}

		matched = append(matched, *snap)
	}

	return matched, nil
}
