package memory

import (
	"context"
	"sync"
	"time"

	"be/internal/domain"
)

type MemoryRepository struct {
	mu            sync.RWMutex
	companies     map[string]*domain.Company
	snapshots     map[string]*domain.IntelligenceSnapshot
	sectorsData   map[string]*domain.FinancialSnapshot
}

func NewMemoryRepository() *MemoryRepository {
	repo := &MemoryRepository{
		companies:   make(map[string]*domain.Company),
		snapshots:   make(map[string]*domain.IntelligenceSnapshot),
		sectorsData: make(map[string]*domain.FinancialSnapshot),
	}
	repo.seedInitialData()
	return repo
}

func (r *MemoryRepository) seedInitialData() {
	initialCompanies := []*domain.Company{
		{
			Symbol:    "BBCA",
			Name:      "Bank Central Asia Tbk",
			Sector:    "Financials",
			SubSector: "Banks",
			MarketCap: 1200000000000000,
			UpdatedAt: time.Now(),
		},
		{
			Symbol:    "TLKM",
			Name:      "Telkom Indonesia (Persero) Tbk",
			Sector:    "Infrastructure",
			SubSector: "Telecommunication",
			MarketCap: 320000000000000,
			UpdatedAt: time.Now(),
		},
		{
			Symbol:    "ASII",
			Name:      "Astra International Tbk",
			Sector:    "Industrials",
			SubSector: "Automotive & Heavy Equipment",
			MarketCap: 210000000000000,
			UpdatedAt: time.Now(),
		},
		{
			Symbol:    "AMRT",
			Name:      "Sumber Alfaria Trijaya Tbk",
			Sector:    "Consumer Non-Cyclicals",
			SubSector: "Food & Staples Retailing",
			MarketCap: 130000000000000,
			UpdatedAt: time.Now(),
		},
		{
			Symbol:    "GOTO",
			Name:      "GoTo Gojek Tokopedia Tbk",
			Sector:    "Technology",
			SubSector: "Software & IT Services",
			MarketCap: 80000000000000,
			UpdatedAt: time.Now(),
		},
	}

	for _, c := range initialCompanies {
		r.companies[c.Symbol] = c
	}
}

// CompanyRepository implementation
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

// SnapshotRepository implementation
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
		if s.RiskScore >= 40 {
			list = append(list, *s)
		}
	}
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
	if len(list) > limit {
		list = list[:limit]
	}
	return list, nil
}
