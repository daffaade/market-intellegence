package postgres

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strconv"
	"time"

	"be/db/sqlc"
	"be/internal/domain"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
)

// SnapshotRepository implements domain.SnapshotRepository using sqlc.Querier.
type SnapshotRepository struct {
	q sqlc.Querier
}

// NewSnapshotRepository creates a new SnapshotRepository.
func NewSnapshotRepository(q sqlc.Querier) *SnapshotRepository {
	return &SnapshotRepository{q: q}
}

var _ domain.SnapshotRepository = (*SnapshotRepository)(nil)

// GetLatestIntelligence retrieves the latest intelligence snapshot for a given symbol.
// Translates pgx.ErrNoRows to domain.ErrCompanyNotFound.
func (r *SnapshotRepository) GetLatestIntelligence(ctx context.Context, symbol string) (*domain.IntelligenceSnapshot, error) {
	row, err := r.q.GetLatestIntelligence(ctx, symbol)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, domain.ErrCompanyNotFound
		}
		return nil, fmt.Errorf("get latest intelligence for %s: %w", symbol, err)
	}

	snap, err := toDomainIntelligence(row)
	if err != nil {
		return nil, fmt.Errorf("convert intelligence snapshot for %s: %w", symbol, err)
	}
	return &snap, nil
}

// SaveIntelligence persists an intelligence snapshot.
func (r *SnapshotRepository) SaveIntelligence(ctx context.Context, snap *domain.IntelligenceSnapshot) error {
	if snap == nil {
		return errors.New("intelligence snapshot cannot be nil")
	}

	posFactorsBytes, err := marshalJSONBOrDefault(snap.PositiveFactors, []byte("[]"))
	if err != nil {
		return fmt.Errorf("marshal positive_factors: %w", err)
	}

	negFactorsBytes, err := marshalJSONBOrDefault(snap.NegativeFactors, []byte("[]"))
	if err != nil {
		return fmt.Errorf("marshal negative_factors: %w", err)
	}

	supFactorsBytes, err := marshalJSONBOrDefault(snap.SupportingFactors, []byte("[]"))
	if err != nil {
		return fmt.Errorf("marshal supporting_factors: %w", err)
	}

	evidenceBytes, err := marshalJSONBOrDefault(snap.Evidence, []byte("[]"))
	if err != nil {
		return fmt.Errorf("marshal evidence: %w", err)
	}

	params := sqlc.InsertIntelligenceSnapshotParams{
		Symbol:             snap.Symbol,
		OpportunityScore:   floatToNumeric(snap.OpportunityScore),
		RiskScore:          floatToNumeric(snap.RiskScore),
		Direction:          snap.Direction,
		Confidence:         snap.Confidence,
		RiskLevel:          snap.RiskLevel,
		IsAnomaly:          snap.IsAnomaly,
		AnomalyScore:       floatToNumeric(snap.AnomalyScore),
		DivergenceDetected: snap.DivergenceDetected,
		PositiveFactors:    posFactorsBytes,
		NegativeFactors:    negFactorsBytes,
		SupportingFactors:  supFactorsBytes,
		Evidence:           evidenceBytes,
		AiResearchSummary: pgtype.Text{
			String: snap.AIResearchSummary,
			Valid:  snap.AIResearchSummary != "",
		},
		ModelVersion: "v3-stacking-rf",
	}

	res, err := r.q.InsertIntelligenceSnapshot(ctx, params)
	if err != nil {
		return fmt.Errorf("save intelligence for %s: %w", snap.Symbol, err)
	}

	snap.ID = res.ID
	if res.CreatedAt.Valid {
		snap.CreatedAt = res.CreatedAt.Time
	}

	return nil
}

// GetLatestSectorsData retrieves the most recent sectors data snapshot for a symbol.
// Translates pgx.ErrNoRows to domain.ErrCompanyNotFound.
func (r *SnapshotRepository) GetLatestSectorsData(ctx context.Context, symbol string) (*domain.FinancialSnapshot, error) {
	row, err := r.q.GetLatestSectorsSnapshot(ctx, symbol)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, domain.ErrCompanyNotFound
		}
		return nil, fmt.Errorf("get latest sectors snapshot for %s: %w", symbol, err)
	}

	snap, err := toDomainFinancialSnapshot(row)
	if err != nil {
		return nil, fmt.Errorf("convert sectors snapshot for %s: %w", symbol, err)
	}
	return &snap, nil
}

// SaveSectorsData persists or updates a sectors data snapshot.
func (r *SnapshotRepository) SaveSectorsData(ctx context.Context, snap *domain.FinancialSnapshot) error {
	if snap == nil {
		return errors.New("financial snapshot cannot be nil")
	}

	valMetricsBytes, err := marshalJSONBOrDefault(snap.ValuationMetrics, []byte("{}"))
	if err != nil {
		return fmt.Errorf("marshal valuation_metrics: %w", err)
	}

	financialsBytes, err := marshalJSONBOrDefault(snap.Financials, []byte("{}"))
	if err != nil {
		return fmt.Errorf("marshal financials: %w", err)
	}

	instFlowBytes, err := marshalJSONBOrDefault(snap.InstitutionalFlow, []byte("{}"))
	if err != nil {
		return fmt.Errorf("marshal institutional_flow: %w", err)
	}

	rawPayloadBytes, err := marshalJSONBOrDefault(snap.RawPayload, []byte("{}"))
	if err != nil {
		return fmt.Errorf("marshal raw_payload: %w", err)
	}

	snapDate := snap.SnapshotDate
	if snapDate.IsZero() {
		snapDate = time.Now()
	}

	params := sqlc.UpsertSectorsSnapshotParams{
		Symbol: snap.Symbol,
		SnapshotDate: pgtype.Date{
			Time:  snapDate,
			Valid: true,
		},
		ValuationMetrics:  valMetricsBytes,
		Financials:        financialsBytes,
		InstitutionalFlow: instFlowBytes,
		RawPayload:        rawPayloadBytes,
	}

	res, err := r.q.UpsertSectorsSnapshot(ctx, params)
	if err != nil {
		return fmt.Errorf("upsert sectors snapshot for %s: %w", snap.Symbol, err)
	}

	if res.FetchedAt.Valid {
		snap.FetchedAt = res.FetchedAt.Time
	}

	return nil
}

// GetTopOpportunities retrieves top opportunities ranked by opportunity score descending.
func (r *SnapshotRepository) GetTopOpportunities(ctx context.Context, limit int) ([]domain.IntelligenceSnapshot, error) {
	rows, err := r.q.GetTopOpportunities(ctx, int32(limit))
	if err != nil {
		return nil, fmt.Errorf("get top opportunities: %w", err)
	}

	result := make([]domain.IntelligenceSnapshot, 0, len(rows))
	for _, row := range rows {
		snap, err := toDomainIntelligence(row)
		if err != nil {
			return nil, fmt.Errorf("convert intelligence snapshot %d: %w", row.ID, err)
		}
		result = append(result, snap)
	}
	return result, nil
}

// GetTopRisks retrieves top risks ranked by risk score descending.
func (r *SnapshotRepository) GetTopRisks(ctx context.Context, limit int) ([]domain.IntelligenceSnapshot, error) {
	rows, err := r.q.GetTopRisks(ctx, int32(limit))
	if err != nil {
		return nil, fmt.Errorf("get top risks: %w", err)
	}

	result := make([]domain.IntelligenceSnapshot, 0, len(rows))
	for _, row := range rows {
		snap, err := toDomainIntelligence(row)
		if err != nil {
			return nil, fmt.Errorf("convert intelligence snapshot %d: %w", row.ID, err)
		}
		result = append(result, snap)
	}
	return result, nil
}

// GetRecentAnomalies retrieves recent anomalies or divergence detections.
func (r *SnapshotRepository) GetRecentAnomalies(ctx context.Context, limit int) ([]domain.IntelligenceSnapshot, error) {
	rows, err := r.q.GetRecentAnomalies(ctx, int32(limit))
	if err != nil {
		return nil, fmt.Errorf("get recent anomalies: %w", err)
	}

	result := make([]domain.IntelligenceSnapshot, 0, len(rows))
	for _, row := range rows {
		snap, err := toDomainIntelligence(row)
		if err != nil {
			return nil, fmt.Errorf("convert intelligence snapshot %d: %w", row.ID, err)
		}
		result = append(result, snap)
	}
	return result, nil
}

func toDomainIntelligence(row sqlc.IntelligenceSnapshot) (domain.IntelligenceSnapshot, error) {
	posFactors, err := unmarshalJSONBOrDefault(row.PositiveFactors, []string{})
	if err != nil {
		return domain.IntelligenceSnapshot{}, fmt.Errorf("unmarshal positive_factors: %w", err)
	}

	negFactors, err := unmarshalJSONBOrDefault(row.NegativeFactors, []string{})
	if err != nil {
		return domain.IntelligenceSnapshot{}, fmt.Errorf("unmarshal negative_factors: %w", err)
	}

	supFactors, err := unmarshalJSONBOrDefault(row.SupportingFactors, []string{})
	if err != nil {
		return domain.IntelligenceSnapshot{}, fmt.Errorf("unmarshal supporting_factors: %w", err)
	}

	evidence, err := unmarshalJSONBOrDefault(row.Evidence, []domain.EvidenceItem{})
	if err != nil {
		return domain.IntelligenceSnapshot{}, fmt.Errorf("unmarshal evidence: %w", err)
	}

	var summary string
	if row.AiResearchSummary.Valid {
		summary = row.AiResearchSummary.String
	}

	var createdAt time.Time
	if row.CreatedAt.Valid {
		createdAt = row.CreatedAt.Time
	}

	return domain.IntelligenceSnapshot{
		ID:                 row.ID,
		Symbol:             row.Symbol,
		OpportunityScore:   numericToFloat(row.OpportunityScore),
		RiskScore:          numericToFloat(row.RiskScore),
		Direction:          row.Direction,
		Confidence:         row.Confidence,
		RiskLevel:          row.RiskLevel,
		IsAnomaly:          row.IsAnomaly,
		AnomalyScore:       numericToFloat(row.AnomalyScore),
		DivergenceDetected: row.DivergenceDetected,
		PositiveFactors:    posFactors,
		NegativeFactors:    negFactors,
		SupportingFactors:  supFactors,
		Evidence:           evidence,
		WhatChanged:        []domain.WhatChangedItem{},
		PeerComparison:     []domain.PeerComparisonItem{},
		AIResearchSummary:  summary,
		Disclaimer:         "",
		IsCached:           false,
		CreatedAt:          createdAt,
	}, nil
}

func toDomainFinancialSnapshot(row sqlc.SectorsDataSnapshot) (domain.FinancialSnapshot, error) {
	valMetrics, err := unmarshalJSONBOrDefault(row.ValuationMetrics, map[string]interface{}{})
	if err != nil {
		return domain.FinancialSnapshot{}, fmt.Errorf("unmarshal valuation_metrics: %w", err)
	}

	financials, err := unmarshalJSONBOrDefault(row.Financials, map[string]interface{}{})
	if err != nil {
		return domain.FinancialSnapshot{}, fmt.Errorf("unmarshal financials: %w", err)
	}

	instFlow, err := unmarshalJSONBOrDefault(row.InstitutionalFlow, map[string]interface{}{})
	if err != nil {
		return domain.FinancialSnapshot{}, fmt.Errorf("unmarshal institutional_flow: %w", err)
	}

	rawPayload, err := unmarshalJSONBOrDefault(row.RawPayload, map[string]interface{}{})
	if err != nil {
		return domain.FinancialSnapshot{}, fmt.Errorf("unmarshal raw_payload: %w", err)
	}

	var snapDate time.Time
	if row.SnapshotDate.Valid {
		snapDate = row.SnapshotDate.Time
	}

	var fetchedAt time.Time
	if row.FetchedAt.Valid {
		fetchedAt = row.FetchedAt.Time
	}

	return domain.FinancialSnapshot{
		Symbol:            row.Symbol,
		SnapshotDate:      snapDate,
		ValuationMetrics:  valMetrics,
		Financials:        financials,
		InstitutionalFlow: instFlow,
		RawPayload:        rawPayload,
		FetchedAt:         fetchedAt,
	}, nil
}

func unmarshalJSONBOrDefault[T any](data []byte, def T) (T, error) {
	if len(data) == 0 || string(data) == "null" {
		return def, nil
	}
	var res T
	if err := json.Unmarshal(data, &res); err != nil {
		return def, err
	}
	return res, nil
}

func marshalJSONBOrDefault(v any, defaultJSON []byte) ([]byte, error) {
	if v == nil {
		return defaultJSON, nil
	}
	b, err := json.Marshal(v)
	if err != nil {
		return nil, err
	}
	if string(b) == "null" {
		return defaultJSON, nil
	}
	return b, nil
}

func numericToFloat(n pgtype.Numeric) float64 {
	if !n.Valid {
		return 0
	}
	f, err := n.Float64Value()
	if err != nil || !f.Valid {
		return 0
	}
	return f.Float64
}

func floatToNumeric(f float64) pgtype.Numeric {
	var num pgtype.Numeric
	_ = num.Scan(strconv.FormatFloat(f, 'f', 2, 64))
	return num
}
