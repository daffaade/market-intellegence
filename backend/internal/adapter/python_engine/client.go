package python_engine

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"math"
	"net/http"
	"net/url"
	"strings"
	"time"

	"be/internal/domain"
)

// DefaultSectors defines the standard set of sectors monitored by sector intelligence.
var DefaultSectors = []string{
	"Financials",
	"Energy",
	"Basic Materials",
	"Consumer Non-Cyclical",
	"Technology",
	"Infrastructure",
	"Healthcare",
	"Industrials",
}

type Client struct {
	baseURL    string
	httpClient *http.Client
}

func NewClient(baseURL string) *Client {
	return &Client{
		baseURL: baseURL,
		httpClient: &http.Client{
			// A cold /api/v1/analyze call (no cache hit in the Python engine) runs forecast,
			// anomaly, divergence, smart-money, and catalyst models together, plus live
			// Sectors/yfinance fetches. Observed cold-call latency ranges widely by symbol
			// (~9s for BBCA, ~43s for BBRI), so a short timeout made the Go client silently
			// time out and fall back to fallbackDeterministicSnapshot even though the engine
			// was healthy and returning real data. This call only happens on a cache miss
			// (24h TTL at this layer, 1h at the engine), so a generous timeout here is safe.
			Timeout: 60 * time.Second,
			Transport: &http.Transport{
				MaxIdleConns:        50,
				MaxIdleConnsPerHost: 10,
				IdleConnTimeout:     60 * time.Second,
			},
		},
	}
}

// Request structure matching ai_engine.routers.analyze.AnalyzeRequest
type pythonAnalyzeRequest struct {
	Symbol            string `json:"symbol"`
	IncludeForecast   bool   `json:"include_forecast"`
	IncludeAnomaly    bool   `json:"include_anomaly"`
	IncludeDivergence bool   `json:"include_divergence"`
	IncludeSmartMoney bool   `json:"include_smart_money"`
	IncludeCatalysts  bool   `json:"include_catalysts"`
}

type pythonOpportunitySignal struct {
	Score           float64  `json:"score"`
	Confidence      string   `json:"confidence"`
	Direction       string   `json:"direction"`
	PositiveFactors []string `json:"positive_factors"`
	NegativeFactors []string `json:"negative_factors"`
	Evidence        []string `json:"evidence"`
}

type pythonRiskSignal struct {
	Score           float64  `json:"score"`
	Level           string   `json:"level"`
	NegativeFactors []string `json:"negative_factors"`
	Evidence        []string `json:"evidence"`
}

type pythonRelativePosition struct {
	Position   string  `json:"position"`
	Diff       float64 `json:"diff"`
	TickerVal  float64 `json:"ticker_val"`
	PeerMedian float64 `json:"peer_median"`
}

type pythonSignificantChange struct {
	Metric        string  `json:"metric"`
	PriorValue    float64 `json:"prior_value"`
	CurrentValue  float64 `json:"current_value"`
	DeltaPct      float64 `json:"delta_pct"`
	ShiftDetected bool    `json:"shift_detected"`
}

type pythonFundamentalDivergence struct {
	PeersContext       *pythonPeersContext                `json:"peers_context"`
	DivergenceScore    float64                            `json:"divergence_score"`
	RelativePositions  map[string]pythonRelativePosition  `json:"relative_positions"`
	SignificantChanges []pythonSignificantChange          `json:"significant_changes"`
}

// pythonPeersContext carries the company reference fields the engine already looked up
// (via Sectors/yfinance) so the Go side can keep `companies` in sync instead of leaving
// market_cap at its seeded placeholder forever.
type pythonPeersContext struct {
	Symbol      string  `json:"symbol"`
	CompanyName string  `json:"company_name"`
	Sector      string  `json:"sector"`
	Industry    string  `json:"industry"`
	MarketCap   int64   `json:"market_cap"`
}

type pythonAnomalyOutput struct {
	Status                   string  `json:"status"`
	IsAnomalousToday         bool    `json:"is_anomalous_today"`
	DetectedAnomaliesCount   int     `json:"detected_anomalies_count"`
	RecentBaselineVolatility float64 `json:"recent_baseline_volatility"`
	AdaptiveContamination    float64 `json:"adaptive_contamination"`
}

type pythonSmartMoneyOutput struct {
	Ticker     string             `json:"ticker"`
	AsOf       string             `json:"as_of"`
	State      string             `json:"state"`
	Score      float64            `json:"score"`
	Components map[string]float64 `json:"components"`
	Confidence string             `json:"confidence"`
	Evidence   []string           `json:"evidence"`
}

type pythonCatalystEventOutput struct {
	Date       string   `json:"date"`
	Type       string   `json:"type"`
	Layer      string   `json:"layer"`
	Direction  string   `json:"direction"`
	Strength   float64  `json:"strength"`
	Confidence string   `json:"confidence"`
	Evidence   []string `json:"evidence"`
}

type pythonCatalystOutput struct {
	Ticker        string                      `json:"ticker"`
	AsOf          string                      `json:"as_of"`
	CatalystScore float64                     `json:"catalyst_score"`
	NetDirection  string                      `json:"net_direction"`
	Events        []pythonCatalystEventOutput `json:"events"`
}

// Response structure matching ai_engine.routers.analyze output
type pythonAnalyzeResponse struct {
	Symbol                string                       `json:"symbol"`
	Forecast              map[string]interface{}       `json:"forecast"`
	OpportunitySignal     *pythonOpportunitySignal     `json:"opportunity_signal"`
	RiskSignal            *pythonRiskSignal            `json:"risk_signal"`
	FundamentalDivergence *pythonFundamentalDivergence `json:"fundamental_divergence"`
	Anomaly               *pythonAnomalyOutput         `json:"anomaly"`
	SmartMoney            *pythonSmartMoneyOutput      `json:"smart_money"`
	Catalysts             *pythonCatalystOutput        `json:"catalysts"`
	Cached                bool                         `json:"cached"`
}

func (c *Client) Analyze(ctx context.Context, req domain.AnalyzeRequest) (*domain.IntelligenceSnapshot, error) {
	// Call Python FastAPI at /api/v1/analyze
	baseURL := strings.TrimRight(c.baseURL, "/")
	reqURL := fmt.Sprintf("%s/api/v1/analyze", baseURL)
	bodyBytes, err := json.Marshal(pythonAnalyzeRequest{
		Symbol:            req.Symbol,
		IncludeForecast:   true,
		IncludeAnomaly:    req.IncludeAnomaly,
		IncludeDivergence: req.IncludeDivergence,
		IncludeSmartMoney: true,
		IncludeCatalysts:  true,
	})
	if err != nil {
		return nil, fmt.Errorf("marshal request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, reqURL, bytes.NewBuffer(bodyBytes))
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		// Fallback to local deterministic Prototype 3 heuristics if Python service is offline
		return markFallback(fallbackDeterministicSnapshot(req.Symbol)), nil
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return markFallback(fallbackDeterministicSnapshot(req.Symbol)), nil
	}

	var pyResp pythonAnalyzeResponse
	if err := json.NewDecoder(resp.Body).Decode(&pyResp); err != nil {
		return markFallback(fallbackDeterministicSnapshot(req.Symbol)), nil
	}

	// Map into domain snapshot
	snap := &domain.IntelligenceSnapshot{
		Symbol:    pyResp.Symbol,
		CreatedAt: time.Now(),
	}
	if snap.Symbol == "" {
		snap.Symbol = req.Symbol
	}

	// 1. Opportunity Signal
	if pyResp.OpportunitySignal != nil {
		snap.OpportunityScore = pyResp.OpportunitySignal.Score
		snap.Direction = pyResp.OpportunitySignal.Direction
		if snap.Direction == "Positive" {
			snap.Direction = "Bullish"
		} else if snap.Direction == "Negative" {
			snap.Direction = "Bearish"
		}
		snap.Confidence = pyResp.OpportunitySignal.Confidence
		snap.PositiveFactors = pyResp.OpportunitySignal.PositiveFactors
	}

	// 2. Risk Signal
	if pyResp.RiskSignal != nil {
		snap.RiskScore = pyResp.RiskSignal.Score
		snap.RiskLevel = pyResp.RiskSignal.Level
		snap.NegativeFactors = pyResp.RiskSignal.NegativeFactors
	}

	// 3. Anomaly
	if pyResp.Anomaly != nil {
		snap.IsAnomaly = pyResp.Anomaly.IsAnomalousToday || pyResp.Anomaly.DetectedAnomaliesCount > 0
		snap.AnomalyScore = pyResp.Anomaly.RecentBaselineVolatility * 1000
		if snap.AnomalyScore > 100 {
			snap.AnomalyScore = 100
		}
	}

	// 4. Fundamental Divergence & Evidence
	if pyResp.FundamentalDivergence != nil {
		snap.DivergenceDetected = pyResp.FundamentalDivergence.DivergenceScore > 0.5 || len(pyResp.FundamentalDivergence.SignificantChanges) > 0

		if pc := pyResp.FundamentalDivergence.PeersContext; pc != nil {
			snap.CompanyMarketCap = pc.MarketCap
			snap.CompanyName = pc.CompanyName
			snap.CompanySector = pc.Sector
			snap.CompanySubSector = pc.Industry
		}

		// Supporting factors from significant changes
		for _, sc := range pyResp.FundamentalDivergence.SignificantChanges {
			if sc.ShiftDetected {
				snap.SupportingFactors = append(snap.SupportingFactors, fmt.Sprintf("Significant shift detected in %s (delta: %.1f%%)", sc.Metric, sc.DeltaPct))
			}
		}

		// Relative positions to EvidenceItem & PeerComparisonItem
		for metric, pos := range pyResp.FundamentalDivergence.RelativePositions {
			snap.Evidence = append(snap.Evidence, domain.EvidenceItem{
				Metric:       strings.ToUpper(metric),
				CompanyValue: fmt.Sprintf("%.2f", pos.TickerVal),
				PeerMedian:   fmt.Sprintf("%.2f", pos.PeerMedian),
				Position:     pos.Position,
			})
			snap.PeerComparison = append(snap.PeerComparison, domain.PeerComparisonItem{
				Metric:     strings.ToUpper(metric),
				Target:     fmt.Sprintf("%.2f", pos.TickerVal),
				PeerMedian: fmt.Sprintf("%.2f", pos.PeerMedian),
				Position:   pos.Position,
			})
		}

		// Significant changes to WhatChanged
		for _, sc := range pyResp.FundamentalDivergence.SignificantChanges {
			impact := "Neutral"
			if sc.DeltaPct > 0 {
				impact = "Positive"
			} else if sc.DeltaPct < 0 {
				impact = "Negative"
			}
			snap.WhatChanged = append(snap.WhatChanged, domain.WhatChangedItem{
				Metric:   strings.ToUpper(sc.Metric),
				Previous: fmt.Sprintf("%.2f", sc.PriorValue),
				Current:  fmt.Sprintf("%.2f", sc.CurrentValue),
				Delta:    fmt.Sprintf("%+.1f%%", sc.DeltaPct),
				Impact:   impact,
			})
		}
	}

	// 5. Smart Money
	if pyResp.SmartMoney != nil {
		snap.SmartMoney = &domain.SmartMoneySnapshot{
			State:      pyResp.SmartMoney.State,
			Score:      pyResp.SmartMoney.Score,
			Components: pyResp.SmartMoney.Components,
			Confidence: pyResp.SmartMoney.Confidence,
			Evidence:   pyResp.SmartMoney.Evidence,
		}
	}

	// 6. Catalysts
	if pyResp.Catalysts != nil {
		catSnap := &domain.CatalystSnapshot{
			CatalystScore: pyResp.Catalysts.CatalystScore,
			NetDirection:  pyResp.Catalysts.NetDirection,
			Events:        make([]domain.CatalystEvent, 0, len(pyResp.Catalysts.Events)),
		}
		for _, e := range pyResp.Catalysts.Events {
			catSnap.Events = append(catSnap.Events, domain.CatalystEvent{
				Date:       e.Date,
				Type:       e.Type,
				Layer:      e.Layer,
				Direction:  e.Direction,
				Strength:   e.Strength,
				Confidence: e.Confidence,
				Evidence:   e.Evidence,
			})
		}
		snap.Catalysts = catSnap
	}

	// If Evidence is still empty, synthesize from OpportunitySignal.Evidence strings
	if len(snap.Evidence) == 0 && pyResp.OpportunitySignal != nil {
		for _, evStr := range pyResp.OpportunitySignal.Evidence {
			snap.Evidence = append(snap.Evidence, domain.EvidenceItem{
				Metric:       evStr,
				CompanyValue: "-",
				PeerMedian:   "-",
				Position:     "Relevant",
			})
		}
	}

	return snap, nil
}

// GetSectorIntelligence fetches sector-level momentum and constituent metrics from Python engine.
func (c *Client) GetSectorIntelligence(ctx context.Context, sectorName string) (*domain.SectorIntelligence, error) {
	trimmed := strings.TrimSpace(sectorName)
	if trimmed == "" {
		return nil, domain.ErrInvalidSector
	}

	baseURL := strings.TrimRight(c.baseURL, "/")
	reqURL := fmt.Sprintf("%s/api/v1/sector/%s", baseURL, url.PathEscape(trimmed))

	httpReq, err := http.NewRequestWithContext(ctx, http.MethodGet, reqURL, nil)
	if err != nil {
		return nil, fmt.Errorf("create sector request: %w", err)
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		// Fallback to deterministic sector data when Python service is offline
		return fallbackSectorIntelligence(trimmed), nil
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, domain.ErrSectorNotFound
	}

	if resp.StatusCode != http.StatusOK {
		return fallbackSectorIntelligence(trimmed), nil
	}

	var sectorResp domain.SectorIntelligence
	if err := json.NewDecoder(resp.Body).Decode(&sectorResp); err != nil {
		return fallbackSectorIntelligence(trimmed), nil
	}

	if sectorResp.Sector == "" {
		sectorResp.Sector = trimmed
	}

	return &sectorResp, nil
}

// ListSectorIntelligences fetches all default sectors' intelligence snapshots.
func (c *Client) ListSectorIntelligences(ctx context.Context) ([]domain.SectorIntelligence, error) {
	results := make([]domain.SectorIntelligence, 0, len(DefaultSectors))
	for _, secName := range DefaultSectors {
		sec, err := c.GetSectorIntelligence(ctx, secName)
		if err != nil {
			sec = fallbackSectorIntelligence(secName)
		}
		if sec != nil {
			results = append(results, *sec)
		}
	}
	return results, nil
}

// fallbackSectorIntelligence returns deterministic sector intelligence when Python service is offline.
func fallbackSectorIntelligence(sector string) *domain.SectorIntelligence {
	nowStr := time.Now().Format("2006-01-02")
	switch sector {
	case "Financials":
		return &domain.SectorIntelligence{
			Sector:         "Financials",
			AsOf:           nowStr,
			NConstituents:  6,
			LowConfidence:  false,
			MomentumScore:  0.42,
			SentimentLabel: "Bullish",
			RotationRank:   1,
			RotationSignal: "Leading",
			Metrics: domain.SectorMetrics{
				RsVsIhsg20d:        0.035,
				BreadthMa50:        0.83,
				AvgOpportunity:     74.5,
				AvgRisk:            "Low",
				DivergenceCount:    2,
				MedianPePercentile: 0.45,
			},
			Evidence: []string{
				"5 dari 6 saham perbankan utama berada di atas MA50",
				"Net institutional inflow persisten dalam 20 hari perdagangan",
			},
			TopContributors: []string{"BBCA", "BBRI", "BMRI"},
		}
	case "Energy":
		return &domain.SectorIntelligence{
			Sector:         "Energy",
			AsOf:           nowStr,
			NConstituents:  5,
			LowConfidence:  false,
			MomentumScore:  0.28,
			SentimentLabel: "Bullish",
			RotationRank:   2,
			RotationSignal: "Leading",
			Metrics: domain.SectorMetrics{
				RsVsIhsg20d:        0.021,
				BreadthMa50:        0.60,
				AvgOpportunity:     68.0,
				AvgRisk:            "Medium",
				DivergenceCount:    1,
				MedianPePercentile: 0.38,
			},
			Evidence: []string{
				"Kenaikan harga komoditas global mendukung margin",
				"3 dari 5 saham di atas MA50",
			},
			TopContributors: []string{"ADRO", "MEDC"},
		}
	case "Basic Materials":
		return &domain.SectorIntelligence{
			Sector:         "Basic Materials",
			AsOf:           nowStr,
			NConstituents:  5,
			LowConfidence:  false,
			MomentumScore:  -0.12,
			SentimentLabel: "Neutral",
			RotationRank:   5,
			RotationSignal: "Lagging",
			Metrics: domain.SectorMetrics{
				RsVsIhsg20d:        -0.015,
				BreadthMa50:        0.40,
				AvgOpportunity:     55.0,
				AvgRisk:            "Medium",
				DivergenceCount:    1,
				MedianPePercentile: 0.62,
			},
			Evidence: []string{
				"Konsolidasi harga logam dasar menekan momentum",
			},
			TopContributors: []string{"ANTM", "MDKA"},
		}
	case "Consumer Non-Cyclical":
		return &domain.SectorIntelligence{
			Sector:         "Consumer Non-Cyclical",
			AsOf:           nowStr,
			NConstituents:  5,
			LowConfidence:  false,
			MomentumScore:  0.15,
			SentimentLabel: "Neutral",
			RotationRank:   3,
			RotationSignal: "Improving",
			Metrics: domain.SectorMetrics{
				RsVsIhsg20d:        0.008,
				BreadthMa50:        0.60,
				AvgOpportunity:     63.5,
				AvgRisk:            "Low",
				DivergenceCount:    0,
				MedianPePercentile: 0.50,
			},
			Evidence: []string{
				"Daya beli stabil mendorong kinerja emiten FMCG",
			},
			TopContributors: []string{"ICBP", "AMRT"},
		}
	case "Technology":
		return &domain.SectorIntelligence{
			Sector:         "Technology",
			AsOf:           nowStr,
			NConstituents:  3,
			LowConfidence:  false,
			MomentumScore:  -0.35,
			SentimentLabel: "Bearish",
			RotationRank:   7,
			RotationSignal: "Weakening",
			Metrics: domain.SectorMetrics{
				RsVsIhsg20d:        -0.042,
				BreadthMa50:        0.33,
				AvgOpportunity:     48.0,
				AvgRisk:            "High",
				DivergenceCount:    2,
				MedianPePercentile: 0.75,
			},
			Evidence: []string{
				"Tekanan jual investor asing pada saham teknologi berkapitalisasi besar",
			},
			TopContributors: []string{"GOTO", "BUKA"},
		}
	case "Infrastructure":
		return &domain.SectorIntelligence{
			Sector:         "Infrastructure",
			AsOf:           nowStr,
			NConstituents:  5,
			LowConfidence:  false,
			MomentumScore:  0.10,
			SentimentLabel: "Neutral",
			RotationRank:   4,
			RotationSignal: "Improving",
			Metrics: domain.SectorMetrics{
				RsVsIhsg20d:        0.005,
				BreadthMa50:        0.60,
				AvgOpportunity:     62.0,
				AvgRisk:            "Low",
				DivergenceCount:    0,
				MedianPePercentile: 0.42,
			},
			Evidence: []string{
				"Defensif dengan arus kas stabil dari telekomunikasi dan menara",
			},
			TopContributors: []string{"TLKM", "ISAT"},
		}
	case "Healthcare":
		return &domain.SectorIntelligence{
			Sector:         "Healthcare",
			AsOf:           nowStr,
			NConstituents:  4,
			LowConfidence:  false,
			MomentumScore:  -0.05,
			SentimentLabel: "Neutral",
			RotationRank:   6,
			RotationSignal: "Lagging",
			Metrics: domain.SectorMetrics{
				RsVsIhsg20d:        -0.008,
				BreadthMa50:        0.50,
				AvgOpportunity:     58.0,
				AvgRisk:            "Low",
				DivergenceCount:    0,
				MedianPePercentile: 0.55,
			},
			Evidence: []string{
				"Pergerakan stabil sejalan dengan rata-rata historis",
			},
			TopContributors: []string{"KLBF", "MIKA"},
		}
	case "Industrials":
		return &domain.SectorIntelligence{
			Sector:         "Industrials",
			AsOf:           nowStr,
			NConstituents:  4,
			LowConfidence:  false,
			MomentumScore:  0.08,
			SentimentLabel: "Neutral",
			RotationRank:   5,
			RotationSignal: "Improving",
			Metrics: domain.SectorMetrics{
				RsVsIhsg20d:        0.002,
				BreadthMa50:        0.50,
				AvgOpportunity:     61.0,
				AvgRisk:            "Medium",
				DivergenceCount:    1,
				MedianPePercentile: 0.48,
			},
			Evidence: []string{
				"Aktivitas manufaktur stabil mendukung permintaan alat berat",
			},
			TopContributors: []string{"ASII", "UNTR"},
		}
	default:
		return &domain.SectorIntelligence{
			Sector:         sector,
			AsOf:           nowStr,
			NConstituents:  4,
			LowConfidence:  false,
			MomentumScore:  0.05,
			SentimentLabel: "Neutral",
			RotationRank:   4,
			RotationSignal: "Stable",
			Metrics: domain.SectorMetrics{
				RsVsIhsg20d:        0.005,
				BreadthMa50:        0.50,
				AvgOpportunity:     60.0,
				AvgRisk:            "Medium",
				DivergenceCount:    0,
				MedianPePercentile: 0.50,
			},
			Evidence: []string{
				"Pergerakan sektor sejalan dengan indeks acuan IHSG",
			},
			TopContributors: []string{},
		}
	}
}

// markFallback flags a snapshot as heuristic fallback data so callers never persist it
// over a real analysis, and the UI can label it.
func markFallback(snap *domain.IntelligenceSnapshot) *domain.IntelligenceSnapshot {
	if snap != nil {
		snap.IsFallback = true
	}
	return snap
}

// fallbackDeterministicSnapshot guarantees zero demo failure even if Python server is not running
func fallbackDeterministicSnapshot(symbol string) *domain.IntelligenceSnapshot {
	now := time.Now()
	nowStr := now.Format("2006-01-02")
	switch symbol {
	case "BBCA":
		return &domain.IntelligenceSnapshot{
			Symbol:             "BBCA",
			OpportunityScore:   85.5,
			RiskScore:          22.0,
			Direction:          "Bullish",
			Confidence:         "High",
			RiskLevel:          "Low",
			IsAnomaly:          false,
			AnomalyScore:       12.0,
			DivergenceDetected: true,
			PositiveFactors: []string{
				"Pertumbuhan laba bersih mengungguli median perbankan (+6.5% vs peer)",
				"Valuasi P/E 13.8x relatif wajar dengan ROE di atas 21%",
				"Aktivitas transaksi investor institusi meningkat 2.2x",
			},
			NegativeFactors: []string{
				"Dividend yield stabil di 3.2%, relatif moderat",
			},
			SupportingFactors: []string{
				"Akumulasi institusi terjadi di tengah konsolidasi harga",
			},
			Evidence: []domain.EvidenceItem{
				{Metric: "Net Profit Growth", CompanyValue: "15.2%", PeerMedian: "8.7%", Position: "Outperform"},
				{Metric: "P/E Ratio", CompanyValue: "13.8x", PeerMedian: "15.4x", Position: "Cheaper"},
				{Metric: "Institutional Activity", CompanyValue: "+24%", PeerMedian: "+8%", Position: "Stronger"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "Revenue Growth", Previous: "8%", Current: "15%", Delta: "+7%", Impact: "Positive"},
				{Metric: "Institutional Volume", Previous: "+8%", Current: "+24%", Delta: "+16%", Impact: "Stronger"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "P/E Ratio", Target: "13.8x", PeerMedian: "15.4x", Position: "Cheaper"},
				{Metric: "ROE", Target: "21.4%", PeerMedian: "14.2%", Position: "Superior"},
			},
			SmartMoney: &domain.SmartMoneySnapshot{
				State: "Accumulation",
				Score: 0.55,
				Components: map[string]float64{
					"transaction_flow":      0.60,
					"cmf":                   0.45,
					"obv_trend":             0.65,
					"price_flow_divergence": 0.50,
				},
				Confidence: "high",
				Evidence: []string{
					"OBV meningkat 4 dari 5 hari terakhir",
					"CMF(20) = +0.22 menunjukkan tekanan beli institusi",
				},
			},
			Catalysts: &domain.CatalystSnapshot{
				CatalystScore: 0.65,
				NetDirection:  "Positive",
				Events: []domain.CatalystEvent{
					{
						Date:       nowStr,
						Type:       "volume_spike",
						Layer:      "market",
						Direction:  "Positive",
						Strength:   0.75,
						Confidence: "high",
						Evidence:   []string{"Volume perdagangan 2.1x rata-rata 60 hari"},
					},
				},
			},
			CreatedAt: now,
		}
	case "TLKM":
		return &domain.IntelligenceSnapshot{
			Symbol:             "TLKM",
			OpportunityScore:   78.0,
			RiskScore:          32.0,
			Direction:          "Bullish",
			Confidence:         "High",
			RiskLevel:          "Low",
			IsAnomaly:          false,
			AnomalyScore:       14.2,
			DivergenceDetected: true,
			PositiveFactors: []string{
				"Pertumbuhan EBITDA 18% di atas median telekomunikasi (9%)",
				"Valuasi P/E 11.2x di bawah median rekan industri (16.0x)",
				"Terjadi akumulasi volume institusi lokal",
			},
			NegativeFactors: []string{
				"Arus keluar dana asing minor dalam 5 hari terakhir",
			},
			SupportingFactors: []string{
				"Valuasi terkompresi sementara laba operasional membaik",
			},
			Evidence: []domain.EvidenceItem{
				{Metric: "EBITDA Growth", CompanyValue: "18.0%", PeerMedian: "9.0%", Position: "Outperform"},
				{Metric: "P/E Ratio", CompanyValue: "11.2x", PeerMedian: "16.0x", Position: "Cheaper"},
				{Metric: "Volume Ratio", CompanyValue: "2.4x", PeerMedian: "1.0x", Position: "Surge"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "Valuation P/E", Previous: "14.0x", Current: "11.2x", Delta: "-2.8x", Impact: "Attractive"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "Dividend Yield", Target: "4.8%", PeerMedian: "3.2%", Position: "Higher"},
			},
			SmartMoney: &domain.SmartMoneySnapshot{
				State: "Accumulation",
				Score: 0.38,
				Components: map[string]float64{
					"transaction_flow":      0.40,
					"cmf":                   0.30,
					"obv_trend":             0.45,
					"price_flow_divergence": 0.35,
				},
				Confidence: "medium",
				Evidence: []string{
					"Akumulasi institusi terdeteksi pada area support",
				},
			},
			Catalysts: &domain.CatalystSnapshot{
				CatalystScore: 0.50,
				NetDirection:  "Positive",
				Events: []domain.CatalystEvent{
					{
						Date:       nowStr,
						Type:       "breakout_high",
						Layer:      "market",
						Direction:  "Positive",
						Strength:   0.60,
						Confidence: "medium",
						Evidence:   []string{"Rebound teknikal dari MA200"},
					},
				},
			},
			CreatedAt: now,
		}
	case "GOTO":
		return &domain.IntelligenceSnapshot{
			Symbol:             "GOTO",
			OpportunityScore:   42.0,
			RiskScore:          78.0,
			Direction:          "Bearish",
			Confidence:         "Medium",
			RiskLevel:          "High",
			IsAnomaly:          true,
			AnomalyScore:       82.0,
			DivergenceDetected: false,
			PositiveFactors: []string{
				"Perbaikan margin kontribusi positif pada unit on-demand",
			},
			NegativeFactors: []string{
				"Volatilitas harian tinggi (vol_20d > 0.035)",
				"Tekanan jual institusi asing meningkat",
				"Valuasi Price-to-Sales masih relatif tinggi dibanding pertumbuhan",
			},
			SupportingFactors: []string{
				"Anomali volatilitas ekstrem terdeteksi",
			},
			Evidence: []domain.EvidenceItem{
				{Metric: "Volatility (20d)", CompanyValue: "3.8%", PeerMedian: "1.4%", Position: "High Risk"},
				{Metric: "Foreign Flow", CompanyValue: "-42B IDR", PeerMedian: "+5B IDR", Position: "Selling"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "Volatility", Previous: "1.8%", Current: "3.8%", Delta: "+2.0%", Impact: "Elevated Risk"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "Price/Sales", Target: "3.5x", PeerMedian: "2.1x", Position: "Expensive"},
			},
			SmartMoney: &domain.SmartMoneySnapshot{
				State: "Distribution",
				Score: -0.42,
				Components: map[string]float64{
					"transaction_flow":      -0.50,
					"cmf":                   -0.35,
					"obv_trend":             -0.45,
					"price_flow_divergence": -0.38,
				},
				Confidence: "medium",
				Evidence: []string{
					"Distribusi terdeteksi pada volume perdagangan harian",
				},
			},
			Catalysts: &domain.CatalystSnapshot{
				CatalystScore: 0.70,
				NetDirection:  "Negative",
				Events: []domain.CatalystEvent{
					{
						Date:       nowStr,
						Type:       "volume_spike",
						Layer:      "market",
						Direction:  "Negative",
						Strength:   0.70,
						Confidence: "high",
						Evidence:   []string{"Tekanan jual dengan volume tinggi"},
					},
				},
			},
			CreatedAt: now,
		}
	default:
		return &domain.IntelligenceSnapshot{
			Symbol:             symbol,
			OpportunityScore:   65.0,
			RiskScore:          35.0,
			Direction:          "Neutral",
			Confidence:         "Medium",
			RiskLevel:          "Medium",
			IsAnomaly:          false,
			AnomalyScore:       10.0,
			DivergenceDetected: false,
			PositiveFactors: []string{
				"Pertumbuhan fundamental stabil sejalan dengan sektor",
				"Tingkat likuiditas perdagangan normal",
			},
			NegativeFactors: []string{
				"Katalis jangka pendek masih menunggu laporan keuangan kuartalan",
			},
			Evidence: []domain.EvidenceItem{
				{Metric: "Growth", CompanyValue: "10.0%", PeerMedian: "9.5%", Position: "In-line"},
				{Metric: "P/E", CompanyValue: "14.5x", PeerMedian: "15.0x", Position: "Fair"},
			},
			SmartMoney: &domain.SmartMoneySnapshot{
				State: "Neutral",
				Score: 0.05,
				Components: map[string]float64{
					"transaction_flow":      0.0,
					"cmf":                   0.05,
					"obv_trend":             0.05,
					"price_flow_divergence": 0.0,
				},
				Confidence: "low",
				Evidence: []string{
					"Aktivitas institusi dalam batas wajar",
				},
			},
			Catalysts: &domain.CatalystSnapshot{
				CatalystScore: 0.0,
				NetDirection:  "None",
				Events:        []domain.CatalystEvent{},
			},
			CreatedAt: now,
		}
	}
}

// CalculatePortfolioRisk sends portfolio compositions to the Python AI engine or returns a deterministic statistical fallback.
func (c *Client) CalculatePortfolioRisk(ctx context.Context, req domain.PortfolioRiskRequest) (*domain.PortfolioRiskReport, error) {
	if len(req.Portfolio) == 0 {
		return nil, domain.ErrInvalidPortfolio
	}

	period := req.Period
	if period == "" {
		period = "1y"
	}

	payload, err := json.Marshal(map[string]any{
		"portfolio": req.Portfolio,
		"period":    period,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to marshal portfolio request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+"/api/v1/portfolio/risk", bytes.NewBuffer(payload))
	if err != nil {
		return fallbackPortfolioRiskReport(req), nil
	}
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return fallbackPortfolioRiskReport(req), nil
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fallbackPortfolioRiskReport(req), nil
	}

	var report domain.PortfolioRiskReport
	if err := json.NewDecoder(resp.Body).Decode(&report); err != nil {
		return fallbackPortfolioRiskReport(req), nil
	}

	if report.Disclaimer == "" {
		report.Disclaimer = "Informasi dan analisis ini merupakan hasil pemrosesan data riset dan bukan merupakan anjuran investasi personal (Bukan rekomendasi Beli/Jual)."
	}

	return &report, nil
}

func fallbackPortfolioRiskReport(req domain.PortfolioRiskRequest) *domain.PortfolioRiskReport {
	period := req.Period
	if period == "" {
		period = "1y"
	}

	individualVol := make(map[string]float64)
	corrMatrix := make(map[string]map[string]float64)
	covMatrix := make(map[string]map[string]float64)
	riskContrib := make(map[string]float64)
	concentrationRisk := 0.0

	defaultVols := map[string]float64{
		"BBCA": 0.22,
		"BBRI": 0.28,
		"BMRI": 0.26,
		"BBNI": 0.30,
		"TLKM": 0.25,
		"ASII": 0.27,
		"AMRT": 0.24,
		"GOTO": 0.55,
		"ANTM": 0.42,
		"BUMI": 0.58,
	}

	totalWeight := 0.0
	for _, p := range req.Portfolio {
		totalWeight += p.Weight
	}
	if totalWeight <= 0 {
		totalWeight = 1.0
	}

	normalized := make([]domain.PortfolioAssetInput, len(req.Portfolio))
	for i, p := range req.Portfolio {
		normalized[i] = domain.PortfolioAssetInput{
			Ticker: strings.ToUpper(p.Ticker),
			Weight: p.Weight / totalWeight,
		}
	}

	for _, p := range normalized {
		vol, ok := defaultVols[p.Ticker]
		if !ok {
			vol = 0.30
		}
		individualVol[p.Ticker] = vol
		concentrationRisk += p.Weight * p.Weight
	}

	for _, p1 := range normalized {
		corrMatrix[p1.Ticker] = make(map[string]float64)
		covMatrix[p1.Ticker] = make(map[string]float64)
		for _, p2 := range normalized {
			if p1.Ticker == p2.Ticker {
				corrMatrix[p1.Ticker][p2.Ticker] = 1.0
			} else {
				corrMatrix[p1.Ticker][p2.Ticker] = 0.50
			}
			vol1 := individualVol[p1.Ticker]
			vol2 := individualVol[p2.Ticker]
			cov := corrMatrix[p1.Ticker][p2.Ticker] * (vol1 / math.Sqrt(252)) * (vol2 / math.Sqrt(252))
			covMatrix[p1.Ticker][p2.Ticker] = cov
		}
	}

	var portVar float64
	for _, p1 := range normalized {
		for _, p2 := range normalized {
			portVar += p1.Weight * p2.Weight * covMatrix[p1.Ticker][p2.Ticker] * 252
		}
	}
	portVol := math.Sqrt(math.Max(0.01, portVar))

	for _, p := range normalized {
		riskContrib[p.Ticker] = p.Weight
	}

	histVaR := portVol / math.Sqrt(252) * 1.65
	mdd := -portVol * 0.95

	return &domain.PortfolioRiskReport{
		Feature:   "portfolio_risk",
		Status:    "SUCCESS",
		Portfolio: normalized,
		Period:    period,
		Metrics: domain.PortfolioRiskMetrics{
			PortfolioVolatility:  math.Round(portVol*1000) / 1000,
			IndividualVolatility: individualVol,
			CorrelationMatrix:    corrMatrix,
			CovarianceMatrix:     covMatrix,
			RiskContribution:     riskContrib,
			ConcentrationRisk:    math.Round(concentrationRisk*1000) / 1000,
			HistoricalVaR:        math.Round(histVaR*1000) / 1000,
			MaximumDrawdown:      math.Round(mdd*1000) / 1000,
		},
		Metadata: map[string]interface{}{
			"historical_data_source": "fallback_model",
			"data_provider":          "UnifiedData",
			"confidence_level":       0.95,
			"var_method":             "parametric_historical",
			"trading_days_assumed":   252,
		},
		AISummary:  "Estimasi risiko portofolio terhitung secara deterministik (mode fallback) dengan diversifikasi terukur.",
		Disclaimer: "Informasi dan analisis ini merupakan hasil pemrosesan data riset dan bukan merupakan anjuran investasi personal (Bukan rekomendasi Beli/Jual).",
	}
}

// AnalyzeConsumerBehavior sends consumer behavior query to Python AI engine or returns a deterministic fallback report.
func (c *Client) AnalyzeConsumerBehavior(ctx context.Context, req domain.ConsumerBehaviorRequest) (*domain.ConsumerBehaviorReport, error) {
	keyword := strings.TrimSpace(req.Keyword)
	if keyword == "" {
		return nil, domain.ErrEmptyKeyword
	}

	payload, err := json.Marshal(map[string]any{
		"keyword":  keyword,
		"industry": req.Industry,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to marshal consumer request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+"/api/v1/consumer-behavior/analyze", bytes.NewBuffer(payload))
	if err != nil {
		return fallbackConsumerBehaviorReport(req), nil
	}
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return fallbackConsumerBehaviorReport(req), nil
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fallbackConsumerBehaviorReport(req), nil
	}

	var report domain.ConsumerBehaviorReport
	if err := json.NewDecoder(resp.Body).Decode(&report); err != nil {
		return fallbackConsumerBehaviorReport(req), nil
	}

	if report.Disclaimer == "" {
		report.Disclaimer = "Informasi dan analisis ini merupakan hasil pemrosesan data riset dan bukan merupakan anjuran investasi personal (Bukan rekomendasi Beli/Jual)."
	}

	return &report, nil
}

func fallbackConsumerBehaviorReport(req domain.ConsumerBehaviorRequest) *domain.ConsumerBehaviorReport {
	keyword := strings.TrimSpace(req.Keyword)
	industry := strings.TrimSpace(req.Industry)
	if industry == "" {
		industry = "Umum"
	}

	return &domain.ConsumerBehaviorReport{
		Keyword:  keyword,
		Industry: industry,
		ImpactSignal: domain.ConsumerImpactSignal{
			ImpactScore:     50.0,
			ImpactDirection: "Neutral",
			ConfidenceLevel: "Medium",
		},
		Evidence: []domain.ConsumerEvidenceItem{
			{
				Source:      "PyTrends & BPS Fallback",
				Metric:      "Tren Pencarian & Konsumsi",
				Value:       "Indeks 50.0 (Stabil)",
				Description: fmt.Sprintf("Aktivitas tren konsumen untuk kata kunci '%s' berada pada level historis normal.", keyword),
			},
			{
				Source:      "Market Data",
				Metric:      "Sensitivitas Sektor",
				Value:       industry,
				Description: fmt.Sprintf("Dampak ekonomi makro terhadap industri %s berada pada rentang netral.", industry),
			},
		},
		Disclaimer: "Informasi dan analisis ini merupakan hasil pemrosesan data riset dan bukan merupakan anjuran investasi personal (Bukan rekomendasi Beli/Jual).",
	}
}

