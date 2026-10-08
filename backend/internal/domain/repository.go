package domain

import "context"

type CompanyRepository interface {
	GetBySymbol(ctx context.Context, symbol string) (*Company, error)
	ListAll(ctx context.Context) ([]Company, error)
	ListBySector(ctx context.Context, sector string) ([]Company, error)
	Upsert(ctx context.Context, comp *Company) error
}

type SnapshotRepository interface {
	GetLatestIntelligence(ctx context.Context, symbol string) (*IntelligenceSnapshot, error)
	SaveIntelligence(ctx context.Context, snap *IntelligenceSnapshot) error
	GetLatestSectorsData(ctx context.Context, symbol string) (*FinancialSnapshot, error)
	SaveSectorsData(ctx context.Context, snap *FinancialSnapshot) error
	GetTopOpportunities(ctx context.Context, limit int) ([]IntelligenceSnapshot, error)
	GetTopRisks(ctx context.Context, limit int) ([]IntelligenceSnapshot, error)
	GetRecentAnomalies(ctx context.Context, limit int) ([]IntelligenceSnapshot, error)
}
