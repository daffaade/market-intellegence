package domain

import "time"

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

type IntelligenceSnapshot struct {
	ID                 int64                `json:"id"`
	Symbol             string               `json:"symbol"`
	OpportunityScore   float64              `json:"opportunity_score"`
	RiskScore          float64              `json:"risk_score"`
	Direction          string               `json:"direction"`
	Confidence         string               `json:"confidence"`
	RiskLevel          string               `json:"risk_level"`
	IsAnomaly          bool                 `json:"is_anomaly"`
	AnomalyScore       float64              `json:"anomaly_score"`
	DivergenceDetected bool                 `json:"divergence_detected"`
	PositiveFactors    []string             `json:"positive_factors"`
	NegativeFactors    []string             `json:"negative_factors"`
	SupportingFactors  []string             `json:"supporting_factors"`
	Evidence           []EvidenceItem       `json:"evidence"`
	WhatChanged        []WhatChangedItem    `json:"what_changed"`
	PeerComparison     []PeerComparisonItem `json:"peer_comparison"`
	AIResearchSummary  string               `json:"ai_research_summary"`
	Disclaimer         string               `json:"disclaimer"`
	IsCached           bool                 `json:"is_cached"`
	CreatedAt          time.Time            `json:"created_at"`
}
