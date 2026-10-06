package usecase

import (
	"context"
	"strings"

	"be/internal/domain"
)

// ConsumerBehaviorUsecase orchestrates consumer behavior analysis and query validation.
type ConsumerBehaviorUsecase struct {
	provider domain.ConsumerBehaviorProvider
}

// NewConsumerBehaviorUsecase creates a new instance of ConsumerBehaviorUsecase.
func NewConsumerBehaviorUsecase(provider domain.ConsumerBehaviorProvider) *ConsumerBehaviorUsecase {
	return &ConsumerBehaviorUsecase{
		provider: provider,
	}
}

// Analyze validates keyword and industry parameters and delegates to the provider.
func (u *ConsumerBehaviorUsecase) Analyze(ctx context.Context, req domain.ConsumerBehaviorRequest) (*domain.ConsumerBehaviorReport, error) {
	keyword := strings.TrimSpace(req.Keyword)
	if keyword == "" {
		return nil, domain.ErrEmptyKeyword
	}

	industry := strings.TrimSpace(req.Industry)
	if industry == "" {
		industry = "Umum"
	}

	cleanReq := domain.ConsumerBehaviorRequest{
		Keyword:  keyword,
		Industry: industry,
	}

	report, err := u.provider.AnalyzeConsumerBehavior(ctx, cleanReq)
	if err != nil {
		return nil, err
	}

	if report.Disclaimer == "" {
		report.Disclaimer = "Informasi dan analisis ini merupakan hasil pemrosesan data riset dan bukan merupakan anjuran investasi personal (Bukan rekomendasi Beli/Jual)."
	}

	return report, nil
}
