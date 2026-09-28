package tests

import (
	"context"
	"errors"
	"testing"

	"be/internal/adapter/python_engine"
	"be/internal/domain"
	"be/internal/usecase"
)

func TestSectorUsecase_GetSectorAndList(t *testing.T) {
	// Uses client with offline fallback
	client := python_engine.NewClient("http://127.0.0.1:59999")
	uc := usecase.NewSectorUsecase(client)

	sec, err := uc.GetSectorIntelligence(context.Background(), "Financials")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if sec.Sector != "Financials" {
		t.Fatalf("expected Financials, got %s", sec.Sector)
	}

	list, err := uc.ListSectors(context.Background())
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(list) == 0 {
		t.Fatalf("expected non-empty sector list")
	}

	// Test invalid empty sector
	_, err = uc.GetSectorIntelligence(context.Background(), "")
	if err != domain.ErrInvalidSector {
		t.Fatalf("expected ErrInvalidSector, got %v", err)
	}

	// Test whitespace-only sector
	_, err = uc.GetSectorIntelligence(context.Background(), "   ")
	if err != domain.ErrInvalidSector {
		t.Fatalf("expected ErrInvalidSector for whitespace, got %v", err)
	}
}

type mockSectorProvider struct {
	getFunc  func(ctx context.Context, sectorName string) (*domain.SectorIntelligence, error)
	listFunc func(ctx context.Context) ([]domain.SectorIntelligence, error)
}

func (m *mockSectorProvider) GetSectorIntelligence(ctx context.Context, sectorName string) (*domain.SectorIntelligence, error) {
	if m.getFunc != nil {
		return m.getFunc(ctx, sectorName)
	}
	return nil, nil
}

func (m *mockSectorProvider) ListSectorIntelligences(ctx context.Context) ([]domain.SectorIntelligence, error) {
	if m.listFunc != nil {
		return m.listFunc(ctx)
	}
	return nil, nil
}

func TestSectorUsecase_MockProviderErrors(t *testing.T) {
	testErr := errors.New("upstream failed")
	mock := &mockSectorProvider{
		getFunc: func(ctx context.Context, sectorName string) (*domain.SectorIntelligence, error) {
			if sectorName == "Unknown" {
				return nil, domain.ErrSectorNotFound
			}
			return nil, testErr
		},
		listFunc: func(ctx context.Context) ([]domain.SectorIntelligence, error) {
			return nil, testErr
		},
	}

	uc := usecase.NewSectorUsecase(mock)

	// Test upstream error wrapping on GetSectorIntelligence
	_, err := uc.GetSectorIntelligence(context.Background(), "Tech")
	if err == nil || !errors.Is(err, testErr) {
		t.Fatalf("expected wrapped testErr, got %v", err)
	}

	// Test sector not found wrapping
	_, err = uc.GetSectorIntelligence(context.Background(), "Unknown")
	if err == nil || !errors.Is(err, domain.ErrSectorNotFound) {
		t.Fatalf("expected wrapped ErrSectorNotFound, got %v", err)
	}

	// Test upstream error wrapping on ListSectors
	_, err = uc.ListSectors(context.Background())
	if err == nil || !errors.Is(err, testErr) {
		t.Fatalf("expected wrapped testErr, got %v", err)
	}
}
