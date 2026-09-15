package domain

import "errors"

var (
	ErrCompanyNotFound    = errors.New("company not found")
	ErrInvalidSymbol      = errors.New("invalid stock symbol")
	ErrUpstreamTimeout    = errors.New("upstream service timed out")
	ErrQuotaExceeded      = errors.New("sectors api quota exceeded")
	ErrIntelligenceFailed = errors.New("failed to compute intelligence")
)
