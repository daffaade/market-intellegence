package domain

import "context"

// PortfolioAssetInput represents an asset ticker and its assigned weight in a portfolio.
type PortfolioAssetInput struct {
	Ticker string  `json:"ticker"`
	Weight float64 `json:"weight"`
}

// PortfolioRiskRequest defines the parameters for calculating multi-asset portfolio risk.
type PortfolioRiskRequest struct {
	Portfolio []PortfolioAssetInput `json:"portfolio"`
	Period    string                `json:"period"`
}

// PortfolioRiskMetrics encapsulates statistical and risk indicators computed for a portfolio.
type PortfolioRiskMetrics struct {
	PortfolioVolatility  float64                       `json:"portfolio_volatility"`
	IndividualVolatility map[string]float64            `json:"individual_volatility"`
	CorrelationMatrix    map[string]map[string]float64 `json:"correlation_matrix"`
	CovarianceMatrix     map[string]map[string]float64 `json:"covariance_matrix"`
	RiskContribution     map[string]float64            `json:"risk_contribution"`
	ConcentrationRisk    float64                       `json:"concentration_risk"`
	HistoricalVaR        float64                       `json:"historical_var"`
	MaximumDrawdown      float64                       `json:"maximum_drawdown"`
}

// PortfolioRiskReport represents the full analysis report returned by the risk engine.
type PortfolioRiskReport struct {
	Feature    string                 `json:"feature"`
	Status     string                 `json:"status"`
	Portfolio  []PortfolioAssetInput  `json:"portfolio"`
	Period     string                 `json:"period"`
	Metrics    PortfolioRiskMetrics   `json:"metrics"`
	Metadata   map[string]interface{} `json:"metadata"`
	AISummary  string                 `json:"ai_summary,omitempty"`
	Disclaimer string                 `json:"disclaimer"`
}

// PortfolioRiskProvider defines the contract for communicating with the portfolio risk engine.
type PortfolioRiskProvider interface {
	CalculatePortfolioRisk(ctx context.Context, req PortfolioRiskRequest) (*PortfolioRiskReport, error)
}
