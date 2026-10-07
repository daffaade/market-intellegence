-- Persist the parts of an intelligence snapshot that were previously dropped on save,
-- so a cache hit returns the same payload as a fresh engine fetch instead of empty
-- what_changed/peer_comparison and a blocking re-analysis for smart_money/catalysts.
ALTER TABLE intelligence_snapshots
    ADD COLUMN what_changed JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN peer_comparison JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN smart_money JSONB,
    ADD COLUMN catalysts JSONB;
