package domain

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
	PayoutRatio      float64 `json:"payout_ratio"`
}

type Shareholder struct {
	Name            string  `json:"name"`
	SharePercentage float64 `json:"share_percentage"`
	Category        string  `json:"category"`
}

type KeyExecutive struct {
	Name              string `json:"name"`
	Position          string `json:"position"`
	Tenure            string `json:"tenure"`
	InsiderAction     string `json:"insider_action"`
	TransactionAmount string `json:"transaction_amount,omitempty"`
}

type SmartMoneyTransaction struct {
	Date        string `json:"date"`
	Institution string `json:"institution"`
	Action      string `json:"action"`
	Volume      string `json:"volume"`
	ValueIDR    string `json:"value_idr"`
}

type CompanyFundamentals struct {
	Symbol       string                  `json:"symbol"`
	GrowthData   []GrowthData            `json:"growth_data"`
	Dividends    []DividendHistory       `json:"dividends"`
	Shareholders []Shareholder           `json:"shareholders"`
	Executives   []KeyExecutive          `json:"executives"`
	SmartMoney   []SmartMoneyTransaction `json:"smart_money"`
}
