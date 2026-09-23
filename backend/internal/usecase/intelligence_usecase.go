package usecase

import (
	"context"
	"fmt"
	"time"

	"be/internal/domain"
	"be/internal/platform/config"
)

type IntelligenceUsecase struct {
	snapshotRepo domain.SnapshotRepository
	companyRepo  domain.CompanyRepository
	pyClient     domain.IntelligenceEngineClient
	aiClient     domain.AIExplanationClient
	cfg          *config.Config
}

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
		// Jika snapshot masih dalam masa TTL, langsung kembalikan (<5ms)
		ttl := time.Duration(u.cfg.CacheTTLHours) * time.Hour
		if time.Since(cached.CreatedAt) < ttl {
			cached.IsCached = true
			if cached.Disclaimer == "" {
				cached.Disclaimer = LegalDisclaimer
			}
			return cached, nil
		}
	}

	// 2. Cache miss / expired: Panggil Intelligence Engine (Python FastAPI / Heuristics)
	snap, err := u.pyClient.Analyze(ctx, domain.AnalyzeRequest{
		Symbol:            symbol,
		IncludePeer:       true,
		IncludeAnomaly:    true,
		IncludeDivergence: true,
	})
	if err != nil {
		if cached != nil {
			cached.IsCached = true
			return cached, nil
		}
		return nil, fmt.Errorf("intelligence analysis failed: %w", err)
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

	return snap, nil
}
