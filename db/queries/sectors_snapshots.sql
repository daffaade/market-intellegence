-- name: GetLatestSectorsSnapshot :one
SELECT id, symbol, snapshot_date, valuation_metrics, financials, institutional_flow, raw_payload, fetched_at
FROM sectors_data_snapshots
WHERE symbol = $1
ORDER BY snapshot_date DESC, fetched_at DESC
LIMIT 1;

-- name: GetSectorsSnapshotByDate :one
SELECT id, symbol, snapshot_date, valuation_metrics, financials, institutional_flow, raw_payload, fetched_at
FROM sectors_data_snapshots
WHERE symbol = $1 AND snapshot_date = $2
LIMIT 1;

-- name: UpsertSectorsSnapshot :one
INSERT INTO sectors_data_snapshots (
    symbol, snapshot_date, valuation_metrics, financials, institutional_flow, raw_payload, fetched_at
) VALUES (
    $1, $2, $3, $4, $5, $6, NOW()
)
ON CONFLICT (symbol, snapshot_date) DO UPDATE SET
    valuation_metrics = EXCLUDED.valuation_metrics,
    financials = EXCLUDED.financials,
    institutional_flow = EXCLUDED.institutional_flow,
    raw_payload = EXCLUDED.raw_payload,
    fetched_at = NOW()
RETURNING id, symbol, snapshot_date, valuation_metrics, financials, institutional_flow, raw_payload, fetched_at;
