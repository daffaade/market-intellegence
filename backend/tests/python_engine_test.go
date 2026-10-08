package tests

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"be/internal/adapter/python_engine"
	"be/internal/domain"
)

func TestPythonEngineClient_AnalyzeWithNewModels(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/api/v1/analyze" {
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(map[string]any{
				"symbol": "BBCA",
				"opportunity_signal": map[string]any{
					"score":            72.4,
					"direction":        "Bullish",
					"confidence":       "High",
					"positive_factors": []string{"Growth kuat"},
				},
				"risk_signal": map[string]any{
					"score": 18.0,
					"level": "Low",
				},
				"smart_money": map[string]any{
					"state": "Accumulation",
					"score": 0.45,
					"components": map[string]float64{
						"cmf": 0.35,
					},
					"confidence": "medium",
					"evidence":   []string{"Akumulasi terdeteksi"},
				},
				"catalysts": map[string]any{
					"catalyst_score": 0.75,
					"net_direction":  "Positive",
					"events": []map[string]any{
						{
							"type":      "volume_shock",
							"direction": "Positive",
							"strength":  0.8,
							"evidence":  []string{"Volume spike"},
						},
					},
				},
			})
			return
		}
		if r.URL.Path == "/api/v1/sector/Financials" {
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(map[string]any{
				"sector":          "Financials",
				"as_of":           "2026-09-28",
				"n_constituents":  4,
				"momentum_score":  0.32,
				"sentiment_label": "Bullish",
				"metrics": map[string]any{
					"rs_vs_ihsg_20d": 0.024,
					"breadth_ma50":   0.75,
				},
				"evidence": []string{"3 dari 4 saham uptrend"},
			})
			return
		}
		http.NotFound(w, r)
	}))
	defer ts.Close()

	client := python_engine.NewClient(ts.URL)
	snap, err := client.Analyze(context.Background(), domain.AnalyzeRequest{Symbol: "BBCA"})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if snap.SmartMoney == nil || snap.SmartMoney.State != "Accumulation" {
		t.Fatalf("expected smart money Accumulation, got %+v", snap.SmartMoney)
	}
	if snap.Catalysts == nil || snap.Catalysts.CatalystScore != 0.75 {
		t.Fatalf("expected catalyst score 0.75, got %+v", snap.Catalysts)
	}
}

func TestPythonEngineClient_FallbackWhenOffline(t *testing.T) {
	// Point to unreachable port
	client := python_engine.NewClient("http://127.0.0.1:59999")
	snap, err := client.Analyze(context.Background(), domain.AnalyzeRequest{Symbol: "BBCA"})
	if err != nil {
		t.Fatalf("expected fallback snapshot, got error: %v", err)
	}
	if snap.SmartMoney == nil {
		t.Fatalf("expected non-nil fallback SmartMoney")
	}
	if snap.Catalysts == nil {
		t.Fatalf("expected non-nil fallback Catalysts")
	}
}

func TestPythonEngineClient_AnalyzeNon200Fallback(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Error(w, "internal server error", http.StatusInternalServerError)
	}))
	defer ts.Close()

	client := python_engine.NewClient(ts.URL)
	snap, err := client.Analyze(context.Background(), domain.AnalyzeRequest{Symbol: "BBCA"})
	if err != nil {
		t.Fatalf("expected fallback snapshot on 500 error, got error: %v", err)
	}
	if snap == nil || snap.Symbol != "BBCA" {
		t.Fatalf("expected BBCA fallback snapshot, got %+v", snap)
	}
	if snap.SmartMoney == nil {
		t.Fatalf("expected non-nil fallback SmartMoney")
	}
}

func TestPythonEngineClient_PortfolioRisk(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/api/v1/portfolio/risk" && r.Method == http.MethodPost {
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(map[string]any{
				"feature": "portfolio_risk",
				"status":  "SUCCESS",
				"portfolio": []map[string]any{
					{"ticker": "BBCA", "weight": 0.6},
					{"ticker": "BMRI", "weight": 0.4},
				},
				"period": "1y",
				"metrics": map[string]any{
					"portfolio_volatility": 0.28,
					"individual_volatility": map[string]float64{
						"BBCA": 0.25,
						"BMRI": 0.31,
					},
					"correlation_matrix": map[string]map[string]float64{
						"BBCA": {"BBCA": 1.0, "BMRI": 0.62},
						"BMRI": {"BBCA": 0.62, "BMRI": 1.0},
					},
					"concentration_risk": 0.52,
					"historical_var":     0.024,
					"maximum_drawdown":   -0.22,
				},
				"ai_summary": "Portofolio terkonsentrasi di sektor perbankan dengan volatilitas terukur.",
				"disclaimer": "Bukan anjuran investasi",
			})
			return
		}
		http.NotFound(w, r)
	}))
	defer ts.Close()

	client := python_engine.NewClient(ts.URL)
	req := domain.PortfolioRiskRequest{
		Portfolio: []domain.PortfolioAssetInput{
			{Ticker: "BBCA", Weight: 0.6},
			{Ticker: "BMRI", Weight: 0.4},
		},
		Period: "1y",
	}

	report, err := client.CalculatePortfolioRisk(context.Background(), req)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if report.Status != "SUCCESS" {
		t.Fatalf("expected SUCCESS, got %s", report.Status)
	}
	if report.Metrics.PortfolioVolatility != 0.28 {
		t.Fatalf("expected volatility 0.28, got %f", report.Metrics.PortfolioVolatility)
	}
	if report.AISummary == "" {
		t.Fatalf("expected ai summary to be populated")
	}

	// Test Fallback when offline
	offlineClient := python_engine.NewClient("http://127.0.0.1:59999")
	fallbackReport, err := offlineClient.CalculatePortfolioRisk(context.Background(), req)
	if err != nil {
		t.Fatalf("expected fallback report when offline, got error: %v", err)
	}
	if fallbackReport.Status != "SUCCESS" {
		t.Fatalf("expected fallback status SUCCESS, got %s", fallbackReport.Status)
	}
	if fallbackReport.Metrics.PortfolioVolatility <= 0 {
		t.Fatalf("expected positive fallback volatility, got %f", fallbackReport.Metrics.PortfolioVolatility)
	}
	if fallbackReport.Disclaimer == "" {
		t.Fatalf("expected non-empty disclaimer")
	}
}




// Regression: every snapshot used to come out anomalous (score 100) with divergence
// detected, because the mapping used the 1-year anomaly count, baseline volatility
// x1000, and the peer distance score. A quiet stock must map to quiet.
func TestPythonEngineClient_AnomalyAndDivergenceMapping(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{
			"symbol": "BBCA",
			"opportunity_signal": {"score": 47.3, "direction": "Negative", "confidence": "Medium"},
			"risk_signal": {"score": 61.3, "level": "Medium"},
			"anomaly": {"status": "success", "is_anomaly": false, "is_anomalous_today": false,
				"anomaly_score": 26.5, "detected_anomalies_count": 20,
				"recent_baseline_volatility": 1.27, "adaptive_contamination": 0.03},
			"fundamental_divergence": {"divergence_score": 0.95, "relative_positions": {}, "significant_changes": []},
			"divergence_signal": {"detected": false, "confidence": "Low"}
		}`))
	}))
	defer ts.Close()

	snap, err := python_engine.NewClient(ts.URL).Analyze(context.Background(), domain.AnalyzeRequest{Symbol: "BBCA"})
	if err != nil {
		t.Fatal(err)
	}
	if snap.IsAnomaly || snap.AnomalyScore != 26.5 {
		t.Errorf("anomaly = %v / %.1f, want false / 26.5", snap.IsAnomaly, snap.AnomalyScore)
	}
	if snap.DivergenceDetected {
		t.Error("divergence must follow divergence_signal.detected, not divergence_score")
	}
}
