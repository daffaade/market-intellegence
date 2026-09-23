package domain

import "context"

type AIExplanationClient interface {
	GenerateSummary(ctx context.Context, snapshot *IntelligenceSnapshot) (string, error)
}
