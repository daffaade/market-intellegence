package domain

import "context"

type AnalyzeRequest struct {
	Symbol            string `json:"symbol"`
	IncludePeer       bool   `json:"include_peer"`
	IncludeAnomaly    bool   `json:"include_anomaly"`
	IncludeDivergence bool   `json:"include_divergence"`
}

type IntelligenceEngineClient interface {
	Analyze(ctx context.Context, req AnalyzeRequest) (*IntelligenceSnapshot, error)
}
