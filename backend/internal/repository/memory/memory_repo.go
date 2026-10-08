package memory

import (
	"context"
	"sort"
	"sync"
	"time"

	"be/internal/domain"
)

type MemoryRepository struct {
	mu          sync.RWMutex
	companies   map[string]*domain.Company
	snapshots   map[string]*domain.IntelligenceSnapshot
	sectorsData map[string]*domain.FinancialSnapshot
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
