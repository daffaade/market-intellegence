package domain

import (
	"context"
	"errors"
)

var (
	ErrSectorNotFound = errors.New("sector not found")
	ErrInvalidSector  = errors.New("invalid sector name")
)

type SectorMetrics struct {
	RsVsIhsg20d        float64 `json:"rs_vs_ihsg_20d"`
	BreadthMa50        float64 `json:"breadth_ma50"`
	AvgOpportunity     float64 `json:"avg_opportunity"`
	AvgRisk            string  `json:"avg_risk"`
	DivergenceCount    int     `json:"divergence_count"`
	MedianPePercentile float64 `json:"median_pe_percentile"`
}

type SectorIntelligence struct {
	Sector          string        `json:"sector"`
	AsOf            string        `json:"as_of"`
	NConstituents   int           `json:"n_constituents"`
	LowConfidence   bool          `json:"low_confidence"`
	MomentumScore   float64       `json:"momentum_score"`
	SentimentLabel  string        `json:"sentiment_label"`
	RotationRank    int           `json:"rotation_rank"`
	RotationSignal  string        `json:"rotation_signal"`
	Metrics         SectorMetrics `json:"metrics"`
	Evidence        []string      `json:"evidence"`
	TopContributors []string      `json:"top_contributors"`
}

type SectorRepository interface {
	GetSector(ctx context.Context, sectorName string) (*SectorIntelligence, error)
	ListSectors(ctx context.Context) ([]SectorIntelligence, error)
}
