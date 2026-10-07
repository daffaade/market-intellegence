ALTER TABLE intelligence_snapshots
    DROP COLUMN IF EXISTS catalysts,
    DROP COLUMN IF EXISTS smart_money,
    DROP COLUMN IF EXISTS peer_comparison,
    DROP COLUMN IF EXISTS what_changed;
