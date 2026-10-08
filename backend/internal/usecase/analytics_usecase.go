package usecase

import (
	"context"
	"sync"
	"time"

	"be/internal/domain"
)

type AnalyticsUsecase struct {
	companyRepo        domain.CompanyRepository
	fundamentalsClient domain.FundamentalsClient

	mu           sync.Mutex
	fundamentals map[string]fundamentalsEntry
}

type fundamentalsEntry struct {
	data      *domain.CompanyFundamentals
	expiresAt time.Time
}

// fundamentalsTTL only spares the engine a disk read; the engine keeps the
// Sectors report for 7 days, which is what actually bounds credit spend.
const fundamentalsTTL = 6 * time.Hour

func NewAnalyticsUsecase(companyRepo domain.CompanyRepository, fc domain.FundamentalsClient) *AnalyticsUsecase {
	return &AnalyticsUsecase{
		companyRepo:        companyRepo,
		fundamentalsClient: fc,
		fundamentals:       make(map[string]fundamentalsEntry),
	}
}

func (u *AnalyticsUsecase) GetFundamentals(ctx context.Context, symbol string) (*domain.CompanyFundamentals, error) {
	if symbol == "" {
		return nil, domain.ErrInvalidSymbol
	}
	// Only tracked companies: an arbitrary symbol would cost a Sectors credit.
	if _, err := u.companyRepo.GetBySymbol(ctx, symbol); err != nil {
		return nil, err
	}

	u.mu.Lock()
	if e, ok := u.fundamentals[symbol]; ok && time.Now().Before(e.expiresAt) {
		u.mu.Unlock()
		return e.data, nil
	}
	u.mu.Unlock()

	f, err := u.fundamentalsClient.GetFundamentals(ctx, symbol)
	if err != nil {
		return nil, err
	}

	u.mu.Lock()
	u.fundamentals[symbol] = fundamentalsEntry{data: f, expiresAt: time.Now().Add(fundamentalsTTL)}
	u.mu.Unlock()
	return f, nil
}
