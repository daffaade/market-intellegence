package domain

import "context"

// GrowthData is one fiscal year of the income statement, in billions of rupiah.
type GrowthData struct {
	Year      string  `json:"year"`
	Revenue   float64 `json:"revenue"`
	NetProfit float64 `json:"net_profit"`
	Margin    float64 `json:"margin"`
}

type DividendHistory struct {
	Year             string  `json:"year"`
	DividendPerShare float64 `json:"dividend_per_share"`
	YieldPercent     float64 `json:"yield_percent"`
	// PayoutRatio is nil when it cannot be derived reliably (e.g. DPS not split-adjusted).
	PayoutRatio *float64 `json:"payout_ratio"`
}

type Shareholder struct {
	Name            string  `json:"name"`
	SharePercentage float64 `json:"share_percentage"`
	Category        string  `json:"category"`
}

// KeyExecutive is a director/commissioner and their reported shareholding, if any.
type KeyExecutive struct {
	Name            string   `json:"name"`
	Position        string   `json:"position"`
	ShareAmount     *int64   `json:"share_amount"`
	SharePercentage *float64 `json:"share_percentage"`
}

// SmartMoneyTransaction is an institution's net change in shares over the reporting period.
type SmartMoneyTransaction struct {
	Institution  string `json:"institution"`
	Action       string `json:"action"`
	SharesChange int64  `json:"shares_change"`
}

type InstitutionalFlowPoint struct {
	Date      string `json:"date"`
	NetShares int64  `json:"net_shares"`
}

type CompanyFundamentals struct {
	Symbol            string                   `json:"symbol"`
	GrowthData        []GrowthData             `json:"growth_data"`
	Dividends         []DividendHistory        `json:"dividends"`
	Shareholders      []Shareholder            `json:"shareholders"`
	Executives        []KeyExecutive           `json:"executives"`
	SmartMoney        []SmartMoneyTransaction  `json:"smart_money"`
	SmartMoneyAsOf    string                   `json:"smart_money_as_of,omitempty"`
	InstitutionalFlow []InstitutionalFlowPoint `json:"institutional_flow"`
	Source            string                   `json:"source"`
	FetchedAt         string                   `json:"fetched_at"`
}

type FundamentalsClient interface {
	GetFundamentals(ctx context.Context, symbol string) (*CompanyFundamentals, error)
}
