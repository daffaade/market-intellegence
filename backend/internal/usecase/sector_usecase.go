package usecase

import (
	"context"
	"fmt"
	"strings"

	"be/internal/domain"
)

// SectorUsecase defines application business rules for sector intelligence.
type SectorUsecase interface {
	GetSectorIntelligence(ctx context.Context, sectorName string) (*domain.SectorIntelligence, error)
	ListSectors(ctx context.Context) ([]domain.SectorIntelligence, error)
}

// SectorProvider defines the upstream provider interface supplying sector metrics.
type SectorProvider interface {
	GetSectorIntelligence(ctx context.Context, sectorName string) (*domain.SectorIntelligence, error)
	ListSectorIntelligences(ctx context.Context) ([]domain.SectorIntelligence, error)
}

type sectorUsecase struct {
	provider SectorProvider
}

// NewSectorUsecase creates a new SectorUsecase instance.
func NewSectorUsecase(provider SectorProvider) SectorUsecase {
	return &sectorUsecase{provider: provider}
}

// GetSectorIntelligence validates sector name and retrieves intelligence snapshot.
func (u *sectorUsecase) GetSectorIntelligence(ctx context.Context, sectorName string) (*domain.SectorIntelligence, error) {
	cleanName := strings.TrimSpace(sectorName)
	if cleanName == "" {
		return nil, domain.ErrInvalidSector
	}

	sec, err := u.provider.GetSectorIntelligence(ctx, cleanName)
	if err != nil {
		return nil, fmt.Errorf("sectorUsecase.GetSectorIntelligence: %w", err)
	}
	return sec, nil
}

// ListSectors retrieves all sector intelligence snapshots.
func (u *sectorUsecase) ListSectors(ctx context.Context) ([]domain.SectorIntelligence, error) {
	list, err := u.provider.ListSectorIntelligences(ctx)
	if err != nil {
		return nil, fmt.Errorf("sectorUsecase.ListSectors: %w", err)
	}
	return list, nil
}
