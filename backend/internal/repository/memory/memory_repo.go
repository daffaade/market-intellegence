package memory

import (
	"context"
	"sort"
	"sync"
	"time"

	"be/internal/domain"
)

type MemoryRepository struct {
	mu                 sync.RWMutex
	companies          map[string]*domain.Company
	snapshots          map[string]*domain.IntelligenceSnapshot
	sectorsData        map[string]*domain.FinancialSnapshot
	fundamentals       map[string]*domain.CompanyFundamentals
	growthTimeline     []domain.MarketGrowthTimelinePoint
	pipelineTelemetry  *domain.PipelineTelemetry
	macroIndicators    []domain.MacroIndicator
	disasterRisks      []domain.DisasterRisk
	portfolioPositions []domain.PortfolioPosition
}

func NewMemoryRepository() *MemoryRepository {
	repo := &MemoryRepository{
		companies:          make(map[string]*domain.Company),
		snapshots:          make(map[string]*domain.IntelligenceSnapshot),
		sectorsData:        make(map[string]*domain.FinancialSnapshot),
		fundamentals:       make(map[string]*domain.CompanyFundamentals),
		growthTimeline:     make([]domain.MarketGrowthTimelinePoint, 0),
		macroIndicators:    make([]domain.MacroIndicator, 0),
		disasterRisks:      make([]domain.DisasterRisk, 0),
		portfolioPositions: make([]domain.PortfolioPosition, 0),
	}
	repo.seedInitialData()
	return repo
}

// NewCompanyRepository returns a MemoryRepository as a CompanyRepository.
func NewCompanyRepository() *MemoryRepository {
	return NewMemoryRepository()
}

// ─────────────────────────────────────────────────────────────────────────────
// CompanyRepository Implementation
// ─────────────────────────────────────────────────────────────────────────────

func (r *MemoryRepository) GetBySymbol(ctx context.Context, symbol string) (*domain.Company, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	comp, ok := r.companies[symbol]
	if !ok {
		return nil, domain.ErrCompanyNotFound
	}
	return comp, nil
}

func (r *MemoryRepository) ListAll(ctx context.Context) ([]domain.Company, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	list := make([]domain.Company, 0, len(r.companies))
	for _, c := range r.companies {
		list = append(list, *c)
	}
	sort.Slice(list, func(i, j int) bool {
		return list[i].MarketCap > list[j].MarketCap
	})
	return list, nil
}

func (r *MemoryRepository) ListBySector(ctx context.Context, sector string) ([]domain.Company, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	var list []domain.Company
	for _, c := range r.companies {
		if c.Sector == sector {
			list = append(list, *c)
		}
	}
	return list, nil
}

func (r *MemoryRepository) Upsert(ctx context.Context, comp *domain.Company) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	comp.UpdatedAt = time.Now()
	r.companies[comp.Symbol] = comp
	return nil
}

// ─────────────────────────────────────────────────────────────────────────────
// SnapshotRepository Implementation
// ─────────────────────────────────────────────────────────────────────────────

func (r *MemoryRepository) GetLatestIntelligence(ctx context.Context, symbol string) (*domain.IntelligenceSnapshot, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	snap, ok := r.snapshots[symbol]
	if !ok {
		return nil, domain.ErrCompanyNotFound
	}
	return snap, nil
}

func (r *MemoryRepository) SaveIntelligence(ctx context.Context, snap *domain.IntelligenceSnapshot) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	snap.CreatedAt = time.Now()
	r.snapshots[snap.Symbol] = snap
	return nil
}

func (r *MemoryRepository) GetLatestSectorsData(ctx context.Context, symbol string) (*domain.FinancialSnapshot, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	data, ok := r.sectorsData[symbol]
	if !ok {
		return nil, domain.ErrCompanyNotFound
	}
	return data, nil
}

func (r *MemoryRepository) SaveSectorsData(ctx context.Context, snap *domain.FinancialSnapshot) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	snap.FetchedAt = time.Now()
	r.sectorsData[snap.Symbol] = snap
	return nil
}

func (r *MemoryRepository) GetTopOpportunities(ctx context.Context, limit int) ([]domain.IntelligenceSnapshot, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	var list []domain.IntelligenceSnapshot
	for _, s := range r.snapshots {
		list = append(list, *s)
	}
	sort.Slice(list, func(i, j int) bool {
		return list[i].OpportunityScore > list[j].OpportunityScore
	})
	if len(list) > limit {
		list = list[:limit]
	}
	return list, nil
}

func (r *MemoryRepository) GetTopRisks(ctx context.Context, limit int) ([]domain.IntelligenceSnapshot, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	var list []domain.IntelligenceSnapshot
	for _, s := range r.snapshots {
		list = append(list, *s)
	}
	sort.Slice(list, func(i, j int) bool {
		return list[i].RiskScore > list[j].RiskScore
	})
	if len(list) > limit {
		list = list[:limit]
	}
	return list, nil
}

func (r *MemoryRepository) GetRecentAnomalies(ctx context.Context, limit int) ([]domain.IntelligenceSnapshot, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	var list []domain.IntelligenceSnapshot
	for _, s := range r.snapshots {
		if s.IsAnomaly || s.DivergenceDetected {
			list = append(list, *s)
		}
	}
	sort.Slice(list, func(i, j int) bool {
		return list[i].AnomalyScore > list[j].AnomalyScore
	})
	if len(list) > limit {
		list = list[:limit]
	}
	return list, nil
}

// ─────────────────────────────────────────────────────────────────────────────
// AnalyticsRepository Implementation
// ─────────────────────────────────────────────────────────────────────────────

func (r *MemoryRepository) GetFundamentals(ctx context.Context, symbol string) (*domain.CompanyFundamentals, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if f, ok := r.fundamentals[symbol]; ok {
		return f, nil
	}

	comp, ok := r.companies[symbol]
	if !ok {
		return nil, domain.ErrCompanyNotFound
	}

	// Dynamic fallback fundamentals generation for emiten without bespoke seed
	return &domain.CompanyFundamentals{
		Symbol: symbol,
		GrowthData: []domain.GrowthData{
			{Year: "2023", Revenue: float64(comp.MarketCap) / 10000000000 * 0.4, NetProfit: float64(comp.MarketCap) / 10000000000 * 0.08, Margin: 20.0},
			{Year: "2024", Revenue: float64(comp.MarketCap) / 10000000000 * 0.45, NetProfit: float64(comp.MarketCap) / 10000000000 * 0.09, Margin: 20.0},
			{Year: "2025", Revenue: float64(comp.MarketCap) / 10000000000 * 0.50, NetProfit: float64(comp.MarketCap) / 10000000000 * 0.11, Margin: 22.0},
			{Year: "2026 (F)", Revenue: float64(comp.MarketCap) / 10000000000 * 0.56, NetProfit: float64(comp.MarketCap) / 10000000000 * 0.13, Margin: 23.2},
		},
		Dividends: []domain.DividendHistory{
			{Year: "2023", DividendPerShare: 120, YieldPercent: 3.5, PayoutRatio: 50.0},
			{Year: "2024", DividendPerShare: 145, YieldPercent: 4.1, PayoutRatio: 52.0},
			{Year: "2025", DividendPerShare: 160, YieldPercent: 4.4, PayoutRatio: 55.0},
		},
		Shareholders: []domain.Shareholder{
			{Name: "Pemegang Saham Pengendali", SharePercentage: 55.0, Category: "INSTITUTIONAL"},
			{Name: "Publik & Ritel", SharePercentage: 45.0, Category: "RETAIL"},
		},
		Executives: []domain.KeyExecutive{
			{Name: "Direktur Utama " + comp.Name, Position: "Presiden Direktur", Tenure: "4 Tahun", InsiderAction: "HELD"},
		},
		SmartMoney: []domain.SmartMoneyTransaction{
			{Date: "2026-09-18", Institution: "Domestic Pension Fund", Action: "ACCUMULATE", Volume: "2,500,000", ValueIDR: "Rp 15.2 M"},
		},
	}, nil
}

func (r *MemoryRepository) GetMarketGrowthTimeline(ctx context.Context) ([]domain.MarketGrowthTimelinePoint, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.growthTimeline, nil
}

func (r *MemoryRepository) GetPipelineTelemetry(ctx context.Context) (*domain.PipelineTelemetry, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.pipelineTelemetry, nil
}

func (r *MemoryRepository) GetMacroIndicators(ctx context.Context) ([]domain.MacroIndicator, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.macroIndicators, nil
}

func (r *MemoryRepository) GetDisasterRisks(ctx context.Context) ([]domain.DisasterRisk, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.disasterRisks, nil
}

func (r *MemoryRepository) GetPortfolioPositions(ctx context.Context) ([]domain.PortfolioPosition, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.portfolioPositions, nil
}
