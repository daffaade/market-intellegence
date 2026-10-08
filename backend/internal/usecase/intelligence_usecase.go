package usecase

import (
	"context"
	"fmt"
	"sync"
	"time"

	"be/internal/domain"
	"be/internal/platform/config"
)

// backgroundRefreshTimeout bounds a stale-while-revalidate refresh, including time spent
// waiting for a slot. A cold engine call has been observed at up to ~45s.
const backgroundRefreshTimeout = 5 * time.Minute

// refreshSlots caps concurrent background refreshes. The Python engine runs its models
// one request at a time, so ten simultaneous refreshes (e.g. a screener load right after
// the cache expires) would just queue there and time out.
var refreshSlots = make(chan struct{}, 2)

type IntelligenceUsecase struct {
	snapshotRepo domain.SnapshotRepository
	companyRepo  domain.CompanyRepository
	pyClient     domain.IntelligenceEngineClient
	aiClient     domain.AIExplanationClient
	cfg          *config.Config

	// refreshing holds symbols with a background refresh in flight, so a burst of
	// requests for one stale symbol triggers a single engine call (and at most one
	// Sectors credit), not one per request.
	refreshing sync.Map
}

// scoringChangedAt marks the last change to how snapshots are computed (scores,
// anomaly/divergence mapping, AI summary). Snapshots older than this are served
// but refreshed in the background, like expired ones. Bump it on every such change.
var scoringChangedAt = time.Date(2026, 10, 8, 15, 15, 0, 0, time.FixedZone("WIB", 7*3600))

const LegalDisclaimer = "Informasi dan analisis ini merupakan hasil pemrosesan data riset dan bukan merupakan anjuran investasi personal (Bukan rekomendasi Beli/Jual)."

func NewIntelligenceUsecase(
	snapshotRepo domain.SnapshotRepository,
	companyRepo domain.CompanyRepository,
	pyClient domain.IntelligenceEngineClient,
	aiClient domain.AIExplanationClient,
	cfg *config.Config,
) *IntelligenceUsecase {
	return &IntelligenceUsecase{
		snapshotRepo: snapshotRepo,
		companyRepo:  companyRepo,
		pyClient:     pyClient,
		aiClient:     aiClient,
		cfg:          cfg,
	}
}

func (u *IntelligenceUsecase) GetCompanyIntelligence(ctx context.Context, symbol string) (*domain.IntelligenceSnapshot, error) {
	if symbol == "" {
		return nil, domain.ErrInvalidSymbol
	}

	// 1. Cek cache snapshot (Zero-Quota-Wasted strategy)
	cached, err := u.snapshotRepo.GetLatestIntelligence(ctx, symbol)
	if err == nil && cached != nil {
		cached.IsCached = true
		if cached.Disclaimer == "" {
			cached.Disclaimer = LegalDisclaimer
		}
		ttl := time.Duration(u.cfg.CacheTTLHours) * time.Hour
		// Expired (or a legacy row saved before smart_money/catalysts were persisted):
		// serve it now and refresh in the background. A synchronous cold engine call
		// takes 9-45s, far past the frontend's request timeout, which would otherwise
		// make the UI silently fall back to mock data.
		if time.Since(cached.CreatedAt) >= ttl || cached.SmartMoney == nil || cached.CreatedAt.Before(scoringChangedAt) {
			u.refreshInBackground(symbol)
		}
		return cached, nil
	}

	// 2. Cache miss: no snapshot at all, so the caller has to wait for the engine.
	return u.fetchAndStore(ctx, symbol)
}

// refreshInBackground re-runs the engine for a symbol detached from the request
// context, at most once at a time per symbol.
func (u *IntelligenceUsecase) refreshInBackground(symbol string) {
	if u.pyClient == nil {
		return
	}
	if _, inFlight := u.refreshing.LoadOrStore(symbol, struct{}{}); inFlight {
		return
	}
	go func() {
		defer u.refreshing.Delete(symbol)
		ctx, cancel := context.WithTimeout(context.Background(), backgroundRefreshTimeout)
		defer cancel()
		select {
		case refreshSlots <- struct{}{}:
			defer func() { <-refreshSlots }()
		case <-ctx.Done():
			return
		}
		_, _ = u.fetchAndStore(ctx, symbol)
	}()
}

// fetchAndStore calls the engine, attaches the AI summary and disclaimer, saves the
// snapshot, and syncs the company reference row.
func (u *IntelligenceUsecase) fetchAndStore(ctx context.Context, symbol string) (*domain.IntelligenceSnapshot, error) {
	snap, err := u.pyClient.Analyze(ctx, domain.AnalyzeRequest{
		Symbol:            symbol,
		IncludePeer:       true,
		IncludeAnomaly:    true,
		IncludeDivergence: true,
	})
	if err != nil {
		return nil, fmt.Errorf("intelligence analysis failed: %w", err)
	}
	if snap.IsFallback {
		// Engine unreachable or too slow: hand back the placeholder (flagged) but do not
		// save it — a saved fallback would be served as "real" for a full TTL, and in a
		// background refresh it would overwrite a genuine older snapshot.
		snap.Disclaimer = LegalDisclaimer
		return snap, nil
	}

	// 3. Generate AI Research Summary
	if u.aiClient != nil && snap.AIResearchSummary == "" {
		summary, err := u.aiClient.GenerateSummary(ctx, snap)
		if err == nil && summary != "" {
			snap.AIResearchSummary = summary
		}
	}

	snap.Disclaimer = LegalDisclaimer
	snap.CreatedAt = time.Now()

	// 4. Simpan ke database/memory cache
	_ = u.snapshotRepo.SaveIntelligence(ctx, snap)

	// 5. Sync company reference data (market_cap/sector) from what the engine already
	// resolved via Sectors/yfinance. Only updates an existing row — this is not where a
	// new symbol gets added to the universe. Best-effort: never fail the request over it.
	if snap.CompanyMarketCap > 0 && u.companyRepo != nil {
		if existing, cErr := u.companyRepo.GetBySymbol(ctx, symbol); cErr == nil && existing != nil {
			existing.MarketCap = snap.CompanyMarketCap
			if snap.CompanyName != "" {
				existing.Name = snap.CompanyName
			}
			if snap.CompanySector != "" {
				existing.Sector = snap.CompanySector
			}
			if snap.CompanySubSector != "" {
				existing.SubSector = snap.CompanySubSector
			}
			_ = u.companyRepo.Upsert(ctx, existing)
		}
	}

	return snap, nil
}
