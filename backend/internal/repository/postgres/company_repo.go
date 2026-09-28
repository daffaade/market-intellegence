package postgres

import (
	"context"
	"errors"
	"fmt"
	"time"

	"be/db/sqlc"
	"be/internal/domain"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
)

// CompanyRepository implements domain.CompanyRepository using sqlc.Querier.
type CompanyRepository struct {
	q sqlc.Querier
}

// NewCompanyRepository creates a new CompanyRepository.
func NewCompanyRepository(q sqlc.Querier) *CompanyRepository {
	return &CompanyRepository{q: q}
}

var _ domain.CompanyRepository = (*CompanyRepository)(nil)

// GetBySymbol retrieves a company by its stock symbol.
// Translates pgx.ErrNoRows to domain.ErrCompanyNotFound.
func (r *CompanyRepository) GetBySymbol(ctx context.Context, symbol string) (*domain.Company, error) {
	row, err := r.q.GetCompany(ctx, symbol)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, domain.ErrCompanyNotFound
		}
		return nil, fmt.Errorf("get company %s: %w", symbol, err)
	}

	comp := toDomainCompany(row)
	return &comp, nil
}

// ListAll retrieves all companies ordered by symbol.
func (r *CompanyRepository) ListAll(ctx context.Context) ([]domain.Company, error) {
	rows, err := r.q.ListCompanies(ctx)
	if err != nil {
		return nil, fmt.Errorf("list all companies: %w", err)
	}

	result := make([]domain.Company, 0, len(rows))
	for _, row := range rows {
		result = append(result, toDomainCompany(row))
	}
	return result, nil
}

// ListBySector retrieves all companies belonging to a specific sector.
func (r *CompanyRepository) ListBySector(ctx context.Context, sector string) ([]domain.Company, error) {
	rows, err := r.q.ListCompaniesBySector(ctx, sector)
	if err != nil {
		return nil, fmt.Errorf("list companies by sector %s: %w", sector, err)
	}

	result := make([]domain.Company, 0, len(rows))
	for _, row := range rows {
		result = append(result, toDomainCompany(row))
	}
	return result, nil
}

// Upsert inserts a new company or updates the existing company record.
func (r *CompanyRepository) Upsert(ctx context.Context, comp *domain.Company) error {
	if comp == nil {
		return errors.New("company cannot be nil")
	}

	params := sqlc.UpsertCompanyParams{
		Symbol: comp.Symbol,
		Name:   comp.Name,
		Sector: comp.Sector,
		SubSector: pgtype.Text{
			String: comp.SubSector,
			Valid:  comp.SubSector != "",
		},
		MarketCap: pgtype.Int8{
			Int64: comp.MarketCap,
			Valid: true,
		},
	}

	res, err := r.q.UpsertCompany(ctx, params)
	if err != nil {
		return fmt.Errorf("upsert company %s: %w", comp.Symbol, err)
	}

	if res.UpdatedAt.Valid {
		comp.UpdatedAt = res.UpdatedAt.Time
	}

	return nil
}

func toDomainCompany(c sqlc.Company) domain.Company {
	var subSector string
	if c.SubSector.Valid {
		subSector = c.SubSector.String
	}
	var marketCap int64
	if c.MarketCap.Valid {
		marketCap = c.MarketCap.Int64
	}
	var updatedAt time.Time
	if c.UpdatedAt.Valid {
		updatedAt = c.UpdatedAt.Time
	}

	return domain.Company{
		Symbol:    c.Symbol,
		Name:      c.Name,
		Sector:    c.Sector,
		SubSector: subSector,
		MarketCap: marketCap,
		UpdatedAt: updatedAt,
	}
}
