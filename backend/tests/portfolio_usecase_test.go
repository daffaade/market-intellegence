package tests

import (
	"context"
	"errors"
	"testing"

	"be/internal/domain"
	"be/internal/usecase"
)

type mockPortfolioRiskProvider struct {
	reportFn func(ctx context.Context, req domain.PortfolioRiskRequest) (*domain.PortfolioRiskReport, error)
}

func (m *mockPortfolioRiskProvider) CalculatePortfolioRisk(ctx context.Context, req domain.PortfolioRiskRequest) (*domain.PortfolioRiskReport, error) {
	if m.reportFn != nil {
		return m.reportFn(ctx, req)
	}
	return nil, errors.New("not implemented")
}

func TestPortfolioUsecase_CalculateRisk(t *testing.T) {
	mockProvider := &mockPortfolioRiskProvider{
		reportFn: func(ctx context.Context, req domain.PortfolioRiskRequest) (*domain.PortfolioRiskReport, error) {
			return &domain.PortfolioRiskReport{
				Status:    "SUCCESS",
				Portfolio: req.Portfolio,
				Period:    req.Period,
				Metrics: domain.PortfolioRiskMetrics{
					PortfolioVolatility: 0.22,
				},
				Disclaimer: "Bukan anjuran investasi",
			}, nil
		},
	}

	u := usecase.NewPortfolioUsecase(mockProvider)

	// Valid case with percentage weights (e.g. 60 and 40)
	req := domain.PortfolioRiskRequest{
		Portfolio: []domain.PortfolioAssetInput{
			{Ticker: "bbca", Weight: 60},
			{Ticker: "bmri", Weight: 40},
		},
		Period: "",
	}

	report, err := u.CalculateRisk(context.Background(), req)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if report.Period != "1y" {
		t.Fatalf("expected default period 1y, got %s", report.Period)
	}
	// Check weights were normalized to sum to 1.0
	if report.Portfolio[0].Ticker != "BBCA" || report.Portfolio[0].Weight != 0.6 {
		t.Fatalf("expected normalized BBCA with weight 0.6, got %+v", report.Portfolio[0])
	}
	if report.Portfolio[1].Ticker != "BMRI" || report.Portfolio[1].Weight != 0.4 {
		t.Fatalf("expected normalized BMRI with weight 0.4, got %+v", report.Portfolio[1])
	}

	// Invalid empty portfolio
	emptyReq := domain.PortfolioRiskRequest{
		Portfolio: []domain.PortfolioAssetInput{},
	}
	_, err = u.CalculateRisk(context.Background(), emptyReq)
	if !errors.Is(err, domain.ErrInvalidPortfolio) {
		t.Fatalf("expected ErrInvalidPortfolio, got: %v", err)
	}
}
