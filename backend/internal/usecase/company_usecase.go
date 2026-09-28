package usecase

import (
	"context"
	"be/internal/domain"
)

type CompanyUsecase struct {
	companyRepo domain.CompanyRepository
}

func NewCompanyUsecase(repo domain.CompanyRepository) *CompanyUsecase {
	return &CompanyUsecase{companyRepo: repo}
}

func (u *CompanyUsecase) ListCompanies(ctx context.Context) ([]domain.Company, error) {
	return u.companyRepo.ListAll(ctx)
}

func (u *CompanyUsecase) GetCompany(ctx context.Context, symbol string) (*domain.Company, error) {
	if symbol == "" {
		return nil, domain.ErrInvalidSymbol
	}
	return u.companyRepo.GetBySymbol(ctx, symbol)
}
