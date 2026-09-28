-- name: GetLatestIntelligence :one
SELECT * FROM intelligence_snapshots
WHERE symbol = $1
ORDER BY created_at DESC
LIMIT 1;

-- name: InsertIntelligenceSnapshot :one
INSERT INTO intelligence_snapshots (
    symbol, opportunity_score, risk_score, direction, confidence, risk_level,
    is_anomaly, anomaly_score, divergence_detected, positive_factors, negative_factors,
    supporting_factors, evidence, ai_research_summary, model_version, created_at
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, NOW()
)
RETURNING *;

-- name: GetTopOpportunities :many
SELECT * FROM intelligence_snapshots
ORDER BY opportunity_score DESC, created_at DESC
LIMIT $1;

-- name: GetTopRisks :many
SELECT * FROM intelligence_snapshots
ORDER BY risk_score DESC, created_at DESC
LIMIT $1;

-- name: GetRecentAnomalies :many
SELECT * FROM intelligence_snapshots
WHERE is_anomaly = true OR divergence_detected = true
ORDER BY created_at DESC
LIMIT $1;
