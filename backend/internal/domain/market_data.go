package domain

import (
	"context"
	"encoding/json"
)

// MarketDataClient serves yfinance-derived series from the Python engine as opaque JSON.
// The backend only gates and caches these; their shape is owned by the engine and the UI.
type MarketDataClient interface {
	GetEngineJSON(ctx context.Context, path string) (json.RawMessage, error)
}
