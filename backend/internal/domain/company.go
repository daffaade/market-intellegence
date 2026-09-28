package domain

import "time"

type Company struct {
	Symbol    string    `json:"symbol"`
	Name      string    `json:"name"`
	Sector    string    `json:"sector"`
	SubSector string    `json:"sub_sector"`
	MarketCap int64     `json:"market_cap"`
	UpdatedAt time.Time `json:"updated_at"`
}

type FinancialSnapshot struct {
	Symbol            string                 `json:"symbol"`
	SnapshotDate      time.Time              `json:"snapshot_date"`
	ValuationMetrics  map[string]interface{} `json:"valuation_metrics"`
	Financials        map[string]interface{} `json:"financials"`
	InstitutionalFlow map[string]interface{} `json:"institutional_flow"`
	RawPayload        map[string]interface{} `json:"raw_payload"`
	FetchedAt         time.Time              `json:"fetched_at"`
}
