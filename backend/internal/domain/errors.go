package domain

import "errors"

var (
	ErrCompanyNotFound    = errors.New("company not found")
	ErrInvalidSymbol      = errors.New("invalid stock symbol")
	ErrUpstreamTimeout    = errors.New("upstream service timed out")
	ErrQuotaExceeded      = errors.New("sectors api quota exceeded")
	ErrIntelligenceFailed = errors.New("failed to compute intelligence")
	ErrInvalidPortfolio   = errors.New("invalid portfolio composition")
	ErrEmptyKeyword       = errors.New("keyword cannot be empty")
)

var ErrFundamentalsUnavailable = errors.New("fundamentals unavailable from upstream")

var ErrUpstreamUnavailable = errors.New("upstream data source unavailable")
