package tests

import (
	"context"
	"errors"
	"testing"

	"be/internal/domain"
	"be/internal/usecase"
)

type mockConsumerBehaviorProvider struct {
	analyzeFn func(ctx context.Context, req domain.ConsumerBehaviorRequest) (*domain.ConsumerBehaviorReport, error)
}

func (m *mockConsumerBehaviorProvider) AnalyzeConsumerBehavior(ctx context.Context, req domain.ConsumerBehaviorRequest) (*domain.ConsumerBehaviorReport, error) {
	if m.analyzeFn != nil {
		return m.analyzeFn(ctx, req)
	}
	return nil, errors.New("not implemented")
}

func TestConsumerBehaviorUsecase_Analyze(t *testing.T) {
	mockProvider := &mockConsumerBehaviorProvider{
		analyzeFn: func(ctx context.Context, req domain.ConsumerBehaviorRequest) (*domain.ConsumerBehaviorReport, error) {
			return &domain.ConsumerBehaviorReport{
				Keyword:  req.Keyword,
				Industry: req.Industry,
				ImpactSignal: domain.ConsumerImpactSignal{
					ImpactScore:     65.0,
					ImpactDirection: "Bullish",
					ConfidenceLevel: "High",
				},
				Disclaimer: "Bukan anjuran investasi",
			}, nil
		},
	}

	u := usecase.NewConsumerBehaviorUsecase(mockProvider)

	// Valid case
	req := domain.ConsumerBehaviorRequest{
		Keyword:  "  otomotif  ",
		Industry: "",
	}

	report, err := u.Analyze(context.Background(), req)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if report.Keyword != "otomotif" {
		t.Fatalf("expected trimmed keyword otomotif, got %s", report.Keyword)
	}
	if report.Industry != "Umum" {
		t.Fatalf("expected default industry Umum, got %s", report.Industry)
	}

	// Empty keyword case
	emptyReq := domain.ConsumerBehaviorRequest{
		Keyword: "   ",
	}
	_, err = u.Analyze(context.Background(), emptyReq)
	if !errors.Is(err, domain.ErrEmptyKeyword) {
		t.Fatalf("expected ErrEmptyKeyword, got: %v", err)
	}
}
