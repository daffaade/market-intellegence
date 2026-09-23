-- 1. Master emiten & sektor
CREATE TABLE companies (
    symbol VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    sector VARCHAR(100) NOT NULL,
    sub_sector VARCHAR(100),
    market_cap BIGINT DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_companies_sector ON companies(sector);

-- 2. Snapshot Data Sectors API (Proteksi Kuota 1.000 Credits)
CREATE TABLE sectors_data_snapshots (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL REFERENCES companies(symbol) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
    valuation_metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    financials JSONB NOT NULL DEFAULT '{}'::jsonb,
    institutional_flow JSONB NOT NULL DEFAULT '{}'::jsonb,
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_sectors_symbol_date UNIQUE (symbol, snapshot_date)
);
CREATE INDEX idx_sectors_symbol_date ON sectors_data_snapshots(symbol, snapshot_date DESC);
CREATE INDEX idx_sectors_raw_gin ON sectors_data_snapshots USING gin(raw_payload);

-- 3. Output Intelligence Engine & AI Explanation
CREATE TABLE intelligence_snapshots (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL REFERENCES companies(symbol) ON DELETE CASCADE,
    opportunity_score NUMERIC(5, 2) NOT NULL,
    risk_score NUMERIC(5, 2) NOT NULL,
    direction VARCHAR(20) NOT NULL,
    confidence VARCHAR(20) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    is_anomaly BOOLEAN NOT NULL DEFAULT FALSE,
    anomaly_score NUMERIC(5, 2) DEFAULT 0,
    divergence_detected BOOLEAN NOT NULL DEFAULT FALSE,
    positive_factors JSONB NOT NULL DEFAULT '[]'::jsonb,
    negative_factors JSONB NOT NULL DEFAULT '[]'::jsonb,
    supporting_factors JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    ai_research_summary TEXT,
    model_version VARCHAR(50) NOT NULL DEFAULT 'v3-stacking-rf',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_intel_symbol_time ON intelligence_snapshots(symbol, created_at DESC);
CREATE INDEX idx_intel_scores ON intelligence_snapshots(opportunity_score DESC, risk_score ASC);
