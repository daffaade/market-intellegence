package usecase

import (
	"context"
	"encoding/json"
	"net/url"
	"sort"
	"strings"
	"sync"
	"time"

	"be/internal/domain"
)

// marketDataTTL matches the engine's own cache; price/macro series move daily.
const marketDataTTL = 3 * time.Hour

type MarketDataUsecase struct {
	client      domain.MarketDataClient
	companyRepo domain.CompanyRepository

	mu    sync.Mutex
	cache map[string]rawEntry
}

type rawEntry struct {
	data      json.RawMessage
	expiresAt time.Time
}

func NewMarketDataUsecase(client domain.MarketDataClient, companyRepo domain.CompanyRepository) *MarketDataUsecase {
	return &MarketDataUsecase{client: client, companyRepo: companyRepo, cache: make(map[string]rawEntry)}
}

func (u *MarketDataUsecase) get(ctx context.Context, path string) (json.RawMessage, error) {
	u.mu.Lock()
	if e, ok := u.cache[path]; ok && time.Now().Before(e.expiresAt) {
		u.mu.Unlock()
		return e.data, nil
	}
	u.mu.Unlock()

	data, err := u.client.GetEngineJSON(ctx, path)
	if err != nil {
		return nil, err
	}
	u.mu.Lock()
	u.cache[path] = rawEntry{data: data, expiresAt: time.Now().Add(marketDataTTL)}
	u.mu.Unlock()
	return data, nil
}

// GetPerformance returns weekly closes for every tracked company over the last year.
func (u *MarketDataUsecase) GetPerformance(ctx context.Context) (json.RawMessage, error) {
	companies, err := u.companyRepo.ListAll(ctx)
	if err != nil {
		return nil, err
	}
	symbols := make([]string, 0, len(companies))
	for _, c := range companies {
		symbols = append(symbols, c.Symbol)
	}
	sort.Strings(symbols)
	return u.get(ctx, "/api/v1/market/performance?symbols="+url.QueryEscape(strings.Join(symbols, ",")))
}

func (u *MarketDataUsecase) GetMacroSnapshot(ctx context.Context) (json.RawMessage, error) {
	return u.get(ctx, "/api/v1/macro/snapshot")
}

func (u *MarketDataUsecase) GetCorporateEvents(ctx context.Context, symbol string) (json.RawMessage, error) {
	if symbol == "" {
		return nil, domain.ErrInvalidSymbol
	}
	if _, err := u.companyRepo.GetBySymbol(ctx, symbol); err != nil {
		return nil, err
	}
	return u.get(ctx, "/api/v1/events/"+url.PathEscape(symbol))
}

// GetMacroSensitivity returns the stock's weekly-return betas on IHSG and macro variables.
func (u *MarketDataUsecase) GetMacroSensitivity(ctx context.Context, symbol string) (json.RawMessage, error) {
	if symbol == "" {
		return nil, domain.ErrInvalidSymbol
	}
	if _, err := u.companyRepo.GetBySymbol(ctx, symbol); err != nil {
		return nil, err
	}
	return u.get(ctx, "/api/v1/macro/sensitivity/"+url.PathEscape(symbol))
}

// GetPipelineSources reports the data sources and the freshness of their caches.
// Not cached here: it only reads local files on the engine side.
func (u *MarketDataUsecase) GetPipelineSources(ctx context.Context) (json.RawMessage, error) {
	return u.client.GetEngineJSON(ctx, "/api/v1/pipeline/sources")
}

// GetSectors returns relative strength, breadth and rotation for every IDX sector.
func (u *MarketDataUsecase) GetSectors(ctx context.Context) (json.RawMessage, error) {
	return u.get(ctx, "/api/v1/sector/")
}

// GetConsumerBehavior relates Google search interest for a keyword to a sector's stocks.
func (u *MarketDataUsecase) GetConsumerBehavior(ctx context.Context, keyword, industry string) (json.RawMessage, error) {
	keyword, industry = strings.ToLower(strings.TrimSpace(keyword)), strings.TrimSpace(industry)
	if keyword == "" || industry == "" || len(keyword) > 60 {
		return nil, domain.ErrEmptyKeyword
	}
	q := url.Values{"keyword": {keyword}, "industry": {industry}}
	return u.get(ctx, "/api/v1/consumer-behavior/analyze?"+q.Encode())
}
