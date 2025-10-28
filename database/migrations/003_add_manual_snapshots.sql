-- Manual snapshots for tracking user assets across different wallets
CREATE TABLE t_user_manual_snapshots (
    snapshot_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES t_users(user_id),
    snapshot_date DATE NOT NULL,
    binance_value NUMERIC(18,2) NOT NULL DEFAULT 0,
    ledger_value NUMERIC(18,2) NOT NULL DEFAULT 0,
    defi_value NUMERIC(18,2) NOT NULL DEFAULT 0,
    other_value NUMERIC(18,2) NOT NULL DEFAULT 0,
    total_value NUMERIC(18,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster queries by user and date
CREATE INDEX idx_manual_snapshots_user_date 
ON t_user_manual_snapshots(user_id, snapshot_date);