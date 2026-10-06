package domain

import "context"

// ConsumerBehaviorRequest defines query parameters for consumer behavior analysis.
type ConsumerBehaviorRequest struct {
	Keyword  string `json:"keyword"`
	Industry string `json:"industry"`
}

// ConsumerImpactSignal encapsulates the computed score and sentiment direction.
type ConsumerImpactSignal struct {
	ImpactScore     float64 `json:"impact_score"`
	ImpactDirection string  `json:"impact_direction"`
	ConfidenceLevel string  `json:"confidence_level"`
}

// ConsumerEvidenceItem represents a piece of supporting evidence from PyTrends or BPS data.
type ConsumerEvidenceItem struct {
	Source      string `json:"source"`
	Metric      string `json:"metric"`
	Value       string `json:"value"`
	Description string `json:"description"`
}

// ConsumerBehaviorReport represents the full analysis report for consumer behavior.
type ConsumerBehaviorReport struct {
	Keyword      string                 `json:"keyword"`
	Industry     string                 `json:"industry"`
	ImpactSignal ConsumerImpactSignal   `json:"impact_signal"`
	Evidence     []ConsumerEvidenceItem `json:"evidence"`
	Disclaimer   string                 `json:"disclaimer"`
}

// ConsumerBehaviorProvider defines the contract for communicating with the consumer behavior model.
type ConsumerBehaviorProvider interface {
	AnalyzeConsumerBehavior(ctx context.Context, req ConsumerBehaviorRequest) (*ConsumerBehaviorReport, error)
}
