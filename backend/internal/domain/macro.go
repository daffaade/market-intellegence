package domain

type MacroIndicator struct {
	Name                  string `json:"name"`
	Value                 string `json:"value"`
	Trend                 string `json:"trend"` // "UP" | "DOWN" | "STABLE"
	CorrelationWithMarket string `json:"correlation_with_market"`
	ImpactAssessment      string `json:"impact_assessment"`
}

type EventImpact struct {
	EventName         string  `json:"event_name"`
	Date              string  `json:"date"`
	Category          string  `json:"category"`
	PriceReactionPct  float64 `json:"price_reaction_pct"`
	MarketSentiment   string  `json:"market_sentiment"`
}

type DisasterRisk struct {
	Region             string `json:"region"`
	RiskType           string `json:"risk_type"`
	Severity           string `json:"severity"` // "LOW" | "MEDIUM" | "HIGH" | "SEVERE"
	ImpactedOperations string `json:"impacted_operations"`
	MitigationStatus   string `json:"mitigation_status"`
}

type PortfolioPosition struct {
	Symbol           string  `json:"symbol"`
	Name             string  `json:"name"`
	AllocationPct    float64 `json:"allocation_pct"`
	Sector           string  `json:"sector"`
	RiskScore        float64 `json:"risk_score"`
	OpportunityScore float64 `json:"opportunity_score"`
}

type MarketGrowthTimelinePoint map[string]interface{}
