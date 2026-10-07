package usecase

import (
	"context"
	"sort"
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

	// symbol -> sector, from the company list fetched above (reliable regardless of
	// whether a snapshot came from cache or a fresh engine fetch).
	sectorBySymbol := make(map[string]string, len(companies))
	for _, c := range companies {
		sectorBySymbol[c.Symbol] = c.Sector
	}

	type sectorAgg struct {
		scoreSum     float64
		count        int
		anomalyCount int
	}
	sectorAggs := make(map[string]*sectorAgg)

	overview := &MarketOverview{
		TopOpportunities:  make([]domain.IntelligenceSnapshot, 0),
		TopRisks:          make([]domain.IntelligenceSnapshot, 0),
		DetectedAnomalies: make([]domain.IntelligenceSnapshot, 0),
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

		sector := sectorBySymbol[snap.Symbol]
		if sector == "" {
			sector = "Unclassified"
		}
		agg, ok := sectorAggs[sector]
		if !ok {
			agg = &sectorAgg{}
			sectorAggs[sector] = agg
		}
		agg.scoreSum += snap.OpportunityScore
		agg.count++
		if snap.IsAnomaly {
			agg.anomalyCount++
		}
	}

	overview.SectorSummary = make([]SectorStat, 0, len(sectorAggs))
	for sector, agg := range sectorAggs {
		if agg.count == 0 {
			continue
		}
		avg := agg.scoreSum / float64(agg.count)
		sentiment := "Neutral"
		if avg >= 60 {
			sentiment = "Bullish"
		} else if avg <= 40 {
			sentiment = "Bearish"
		}
		overview.SectorSummary = append(overview.SectorSummary, SectorStat{
			Sector:         sector,
			Sentiment:      sentiment,
			AvgOpportunity: avg,
			AnomalyCount:   agg.anomalyCount,
		})
	}
	// Map iteration order is random in Go; sort so the response (and the UI) is stable
	// across requests instead of reshuffling sectors on every refresh.
	sort.Slice(overview.SectorSummary, func(i, j int) bool {
		return overview.SectorSummary[i].AvgOpportunity > overview.SectorSummary[j].AvgOpportunity
	})

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
