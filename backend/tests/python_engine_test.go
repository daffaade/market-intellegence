package tests

import (
	"context"
	"encoding/json"
	"errors"
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

	sec, err := client.GetSectorIntelligence(context.Background(), "Financials")
	if err != nil {
		t.Fatalf("failed to get sector intelligence: %v", err)
	}
	if sec.SentimentLabel != "Bullish" {
		t.Fatalf("expected Bullish, got %s", sec.SentimentLabel)
	}

	// Test sector not found (404)
	_, err = client.GetSectorIntelligence(context.Background(), "NonExistentSector")
	if !errors.Is(err, domain.ErrSectorNotFound) {
		t.Fatalf("expected ErrSectorNotFound, got: %v", err)
	}

	// Test invalid sector
	_, err = client.GetSectorIntelligence(context.Background(), "   ")
	if !errors.Is(err, domain.ErrInvalidSector) {
		t.Fatalf("expected ErrInvalidSector, got: %v", err)
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

	sec, err := client.GetSectorIntelligence(context.Background(), "Financials")
	if err != nil {
		t.Fatalf("expected fallback sector, got error: %v", err)
	}
	if sec.Sector != "Financials" {
		t.Fatalf("expected Financials, got %s", sec.Sector)
	}

	// Test ListSectorIntelligences fallback
	sectors, err := client.ListSectorIntelligences(context.Background())
	if err != nil {
		t.Fatalf("expected fallback sector list, got error: %v", err)
	}
	if len(sectors) != len(python_engine.DefaultSectors) {
		t.Fatalf("expected %d default sectors, got %d", len(python_engine.DefaultSectors), len(sectors))
	}
}
