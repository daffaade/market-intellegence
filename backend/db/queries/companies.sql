-- name: GetCompany :one
SELECT symbol, name, sector, sub_sector, market_cap, created_at, updated_at
FROM companies
WHERE symbol = $1
LIMIT 1;

-- name: ListCompanies :many
SELECT symbol, name, sector, sub_sector, market_cap, created_at, updated_at
FROM companies
ORDER BY symbol ASC;

-- name: ListCompaniesBySector :many
SELECT symbol, name, sector, sub_sector, market_cap, created_at, updated_at
FROM companies
WHERE sector = $1
ORDER BY symbol ASC;

-- name: UpsertCompany :one
INSERT INTO companies (
    symbol, name, sector, sub_sector, market_cap, updated_at
) VALUES (
    $1, $2, $3, $4, $5, NOW()
)
ON CONFLICT (symbol) DO UPDATE SET
    name = EXCLUDED.name,
    sector = EXCLUDED.sector,
    sub_sector = EXCLUDED.sub_sector,
    market_cap = EXCLUDED.market_cap,
    updated_at = NOW()
RETURNING symbol, name, sector, sub_sector, market_cap, created_at, updated_at;
