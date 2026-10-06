package tests

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"testing"

	deliveryhttp "be/internal/delivery/http"
	"be/internal/delivery/http/handler"
	"be/internal/domain"
	"be/internal/usecase"
)

func TestPortfolioAndConsumerEndpoints(t *testing.T) {
	// Setup mock providers
	mockPortfolioProvider := &mockPortfolioRiskProvider{
		reportFn: func(ctx context.Context, req domain.PortfolioRiskRequest) (*domain.PortfolioRiskReport, error) {
			return &domain.PortfolioRiskReport{
				Status:    "SUCCESS",
				Portfolio: req.Portfolio,
				Period:    req.Period,
				Metrics: domain.PortfolioRiskMetrics{
					PortfolioVolatility: 0.25,
					ConcentrationRisk:   0.5,
				},
				Disclaimer: "Bukan anjuran investasi",
			}, nil
		},
	}

	mockConsumerProvider := &mockConsumerBehaviorProvider{
		analyzeFn: func(ctx context.Context, req domain.ConsumerBehaviorRequest) (*domain.ConsumerBehaviorReport, error) {
			return &domain.ConsumerBehaviorReport{
				Keyword:  req.Keyword,
				Industry: req.Industry,
				ImpactSignal: domain.ConsumerImpactSignal{
					ImpactScore:     70.0,
					ImpactDirection: "Bullish",
					ConfidenceLevel: "High",
				},
				Disclaimer: "Bukan anjuran investasi",
			}, nil
		},
	}

	portUsecase := usecase.NewPortfolioUsecase(mockPortfolioProvider)
	consumerUsecase := usecase.NewConsumerBehaviorUsecase(mockConsumerProvider)

	handlers := deliveryhttp.Handlers{
		Portfolio: handler.NewPortfolioHandler(portUsecase),
		Consumer:  handler.NewConsumerHandler(consumerUsecase),
	}

	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	router := deliveryhttp.NewRouter(handlers, logger)

	// 1. Test POST /api/v1/portfolio/risk
	t.Run("POST /api/v1/portfolio/risk - Success", func(t *testing.T) {
		body := map[string]any{
			"portfolio": []map[string]any{
				{"ticker": "BBCA", "weight": 0.6},
				{"ticker": "TLKM", "weight": 0.4},
			},
			"period": "1y",
		}
		jsonBytes, _ := json.Marshal(body)
		req := httptest.NewRequest(http.MethodPost, "/api/v1/portfolio/risk", bytes.NewBuffer(jsonBytes))
		req.Header.Set("Content-Type", "application/json")
		rr := httptest.NewRecorder()

		router.ServeHTTP(rr, req)

		if rr.Code != http.StatusOK {
			t.Fatalf("expected 200 OK, got %d: %s", rr.Code, rr.Body.String())
		}

		var resp map[string]any
		if err := json.Unmarshal(rr.Body.Bytes(), &resp); err != nil {
			t.Fatalf("failed to decode response: %v", err)
		}
		if resp["status"] != "success" {
			t.Fatalf("expected status success, got %v", resp["status"])
		}
	})

	// 2. Test POST /api/v1/portfolio/risk - Invalid empty
	t.Run("POST /api/v1/portfolio/risk - Invalid empty", func(t *testing.T) {
		body := map[string]any{
			"portfolio": []map[string]any{},
		}
		jsonBytes, _ := json.Marshal(body)
		req := httptest.NewRequest(http.MethodPost, "/api/v1/portfolio/risk", bytes.NewBuffer(jsonBytes))
		req.Header.Set("Content-Type", "application/json")
		rr := httptest.NewRecorder()

		router.ServeHTTP(rr, req)

		if rr.Code != http.StatusBadRequest {
			t.Fatalf("expected 400 Bad Request, got %d: %s", rr.Code, rr.Body.String())
		}
	})

	// 3. Test POST /api/v1/consumer-behavior/analyze - Success
	t.Run("POST /api/v1/consumer-behavior/analyze - Success", func(t *testing.T) {
		body := map[string]any{
			"keyword":  "makanan",
			"industry": "makanan & minuman",
		}
		jsonBytes, _ := json.Marshal(body)
		req := httptest.NewRequest(http.MethodPost, "/api/v1/consumer-behavior/analyze", bytes.NewBuffer(jsonBytes))
		req.Header.Set("Content-Type", "application/json")
		rr := httptest.NewRecorder()

		router.ServeHTTP(rr, req)

		if rr.Code != http.StatusOK {
			t.Fatalf("expected 200 OK, got %d: %s", rr.Code, rr.Body.String())
		}

		var resp map[string]any
		if err := json.Unmarshal(rr.Body.Bytes(), &resp); err != nil {
			t.Fatalf("failed to decode response: %v", err)
		}
		if resp["status"] != "success" {
			t.Fatalf("expected status success, got %v", resp["status"])
		}
	})

	// 4. Test GET /api/v1/consumer-behavior/analyze - Success
	t.Run("GET /api/v1/consumer-behavior/analyze - Success", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/api/v1/consumer-behavior/analyze?keyword=otomotif&industry=transportasi", nil)
		rr := httptest.NewRecorder()

		router.ServeHTTP(rr, req)

		if rr.Code != http.StatusOK {
			t.Fatalf("expected 200 OK, got %d: %s", rr.Code, rr.Body.String())
		}
	})
}
