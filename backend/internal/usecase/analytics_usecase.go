package usecase

import (
	"context"

	"be/internal/domain"
)

type AnalyticsUsecase struct {
	analyticsRepo domain.AnalyticsRepository
}

func NewAnalyticsUsecase(repo domain.AnalyticsRepository) *AnalyticsUsecase {
	return &AnalyticsUsecase{analyticsRepo: repo}
}

func (u *AnalyticsUsecase) GetFundamentals(ctx context.Context, symbol string) (*domain.CompanyFundamentals, error) {
	if symbol == "" {
		return nil, domain.ErrInvalidSymbol
	}
	return u.analyticsRepo.GetFundamentals(ctx, symbol)
}

func (u *AnalyticsUsecase) GetMarketGrowthTimeline(ctx context.Context) ([]domain.MarketGrowthTimelinePoint, error) {
	return u.analyticsRepo.GetMarketGrowthTimeline(ctx)
}

func (u *AnalyticsUsecase) GetPipelineTelemetry(ctx context.Context) (*domain.PipelineTelemetry, error) {
	return u.analyticsRepo.GetPipelineTelemetry(ctx)
}

func (u *AnalyticsUsecase) GetMacroIndicators(ctx context.Context) ([]domain.MacroIndicator, error) {
	return u.analyticsRepo.GetMacroIndicators(ctx)
}

func (u *AnalyticsUsecase) GetDisasterRisks(ctx context.Context) ([]domain.DisasterRisk, error) {
	return u.analyticsRepo.GetDisasterRisks(ctx)
}

func (u *AnalyticsUsecase) GetPortfolioPositions(ctx context.Context) ([]domain.PortfolioPosition, error) {
	return u.analyticsRepo.GetPortfolioPositions(ctx)
}
