package usecase

import (
	"context"
	"strings"

	"be/internal/domain"
)

// PortfolioUsecase orchestrates portfolio risk calculations and weight normalization.
type PortfolioUsecase struct {
	provider domain.PortfolioRiskProvider
}

// NewPortfolioUsecase creates a new instance of PortfolioUsecase.
func NewPortfolioUsecase(provider domain.PortfolioRiskProvider) *PortfolioUsecase {
	return &PortfolioUsecase{
		provider: provider,
	}
}

// CalculateRisk normalizes input portfolio weights and invokes the risk provider.
func (u *PortfolioUsecase) CalculateRisk(ctx context.Context, req domain.PortfolioRiskRequest) (*domain.PortfolioRiskReport, error) {
	if len(req.Portfolio) == 0 {
		return nil, domain.ErrInvalidPortfolio
	}

	totalWeight := 0.0
	cleanPortfolio := make([]domain.PortfolioAssetInput, 0, len(req.Portfolio))

	for _, item := range req.Portfolio {
		ticker := strings.ToUpper(strings.TrimSpace(item.Ticker))
		if ticker == "" || item.Weight <= 0 {
			continue
		}
		totalWeight += item.Weight
		cleanPortfolio = append(cleanPortfolio, domain.PortfolioAssetInput{
			Ticker: ticker,
			Weight: item.Weight,
		})
	}

	if len(cleanPortfolio) == 0 || totalWeight <= 0 {
		return nil, domain.ErrInvalidPortfolio
	}

	// Normalize weights so they sum to 1.0 (whether passed as percentages e.g. 60/40 or fractions e.g. 0.6/0.4)
	for i := range cleanPortfolio {
		cleanPortfolio[i].Weight = cleanPortfolio[i].Weight / totalWeight
	}

	period := strings.TrimSpace(req.Period)
	if period == "" {
		period = "1y"
	}

	normReq := domain.PortfolioRiskRequest{
		Portfolio: cleanPortfolio,
		Period:    period,
	}

	report, err := u.provider.CalculatePortfolioRisk(ctx, normReq)
	if err != nil {
		return nil, err
	}

	if report.Disclaimer == "" {
		report.Disclaimer = "Informasi dan analisis ini merupakan hasil pemrosesan data riset dan bukan merupakan anjuran investasi personal (Bukan rekomendasi Beli/Jual)."
	}

	return report, nil
}
