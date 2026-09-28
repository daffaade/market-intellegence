package domain

import (
	"context"
	"time"
)

type SmartMoneySnapshot struct {
	State      string             `json:"state"`
	Score      float64            `json:"score"`
	Components map[string]float64 `json:"components"`
	Confidence string             `json:"confidence"`
	Evidence   []string           `json:"evidence"`
}

type CatalystEvent struct {
	Date       string   `json:"date"`
	Type       string   `json:"type"`
	Layer      string   `json:"layer"`
	Direction  string   `json:"direction"`
	Strength   float64  `json:"strength"`
	Confidence string   `json:"confidence"`
	Evidence   []string `json:"evidence"`
}

type CatalystSnapshot struct {
	CatalystScore float64         `json:"catalyst_score"`
	NetDirection  string          `json:"net_direction"`
	Events        []CatalystEvent `json:"events"`
}

type EvidenceItem struct {
	Metric       string `json:"metric"`
	CompanyValue string `json:"company_value"`
	PeerMedian   string `json:"peer_median"`
	Position     string `json:"position"`
}

type WhatChangedItem struct {
	Metric   string `json:"metric"`
	Previous string `json:"previous"`
	Current  string `json:"current"`
	Delta    string `json:"delta"`
	Impact   string `json:"impact"`
}

type PeerComparisonItem struct {
	Metric     string `json:"metric"`
	Target     string `json:"target"`
	PeerMedian string `json:"peer_median"`
	Position   string `json:"position"`
}

type FundamentalDivergence struct {
	DivergenceScore float64 `json:"divergence_score"`
	Reason          string  `json:"reason,omitempty"`
}

type IntelligenceSnapshot struct {
	ID                    int64                  `json:"id,omitempty"`
	Symbol                string                 `json:"symbol"`
	OpportunityScore      float64                `json:"opportunity_score"`
	RiskScore             float64                `json:"risk_score"`
	RiskLevel             string                 `json:"risk_level"`
	Direction             string                 `json:"direction"`
	Confidence            string                 `json:"confidence"`
	IsAnomaly             bool                   `json:"is_anomaly"`
	AnomalyScore          float64                `json:"anomaly_score,omitempty"`
	AnomalyReason         string                 `json:"anomaly_reason,omitempty"`
	DivergenceDetected    bool                   `json:"divergence_detected,omitempty"`
	PositiveFactors       []string               `json:"positive_factors"`
	NegativeFactors       []string               `json:"negative_factors"`
	SupportingFactors     []string               `json:"supporting_factors,omitempty"`
	Evidence              []EvidenceItem         `json:"evidence,omitempty"`
	WhatChanged           []WhatChangedItem      `json:"what_changed,omitempty"`
	PeerComparison        []PeerComparisonItem   `json:"peer_comparison,omitempty"`
	AIResearchSummary     string                 `json:"ai_research_summary,omitempty"`
	Disclaimer            string                 `json:"disclaimer,omitempty"`
	IsCached              bool                   `json:"is_cached,omitempty"`
	FundamentalDivergence *FundamentalDivergence `json:"fundamental_divergence,omitempty"`
	SmartMoney            *SmartMoneySnapshot    `json:"smart_money,omitempty"`
	Catalysts             *CatalystSnapshot      `json:"catalysts,omitempty"`
	CreatedAt             time.Time              `json:"created_at"`
}

type IntelligenceRepository interface {
	GetLatestSnapshot(ctx context.Context, symbol string) (*IntelligenceSnapshot, error)
	ListSnapshots(ctx context.Context, symbol string, limit int) ([]IntelligenceSnapshot, error)
	SaveSnapshot(ctx context.Context, snapshot *IntelligenceSnapshot) error
}
