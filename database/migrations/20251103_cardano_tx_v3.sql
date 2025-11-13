-- ========================================
-- MIGRATION: Cardano Transactions V3 (DB-first)
-- Date: 2025-11-03
-- Adds relational tables to persist raw Cardano transactions (inputs/outputs),
-- assets metadata, and sync state per wallet. Designed so Portfolio v3 can
-- compute holdings and valuation from DB without calling external APIs first.
-- ========================================

-- Raw transactions fetched from Cardano API (one row per tx per tracked wallet)
CREATE TABLE IF NOT EXISTS t_cardano_transactions (
    tx_hash TEXT PRIMARY KEY,
    wallet_id INTEGER REFERENCES t_wallet(wallet_id) ON DELETE CASCADE,
    address TEXT NOT NULL, -- bech32 wallet address tracked
    block_height INTEGER,
    tx_timestamp TIMESTAMP WITH TIME ZONE,
    status TEXT, -- 'confirmed'/'pending' or free text
    fees_ada NUMERIC(36, 8) DEFAULT 0,
    raw_payload JSONB, -- optional raw json for auditing/debug
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cardano_tx_wallet ON t_cardano_transactions(wallet_id);
CREATE INDEX IF NOT EXISTS idx_cardano_tx_time ON t_cardano_transactions(tx_timestamp DESC);

-- Token/asset metadata seen on-chain
CREATE TABLE IF NOT EXISTS t_cardano_assets (
    policy_id TEXT NOT NULL,
    asset_name_hex TEXT, -- can be null for ADA
    display_name TEXT,   -- resolved human name (ticker-like)
    decimals INTEGER,
    CONSTRAINT pk_cardano_assets PRIMARY KEY (policy_id, asset_name_hex)
);

-- Inputs/Outputs per transaction filtered to the tracked wallet address.
-- One row per IO and per asset (ADA as lovelace only; tokens as policy/name pairs)
CREATE TABLE IF NOT EXISTS t_cardano_tx_io (
    io_id BIGSERIAL PRIMARY KEY,
    tx_hash TEXT NOT NULL REFERENCES t_cardano_transactions(tx_hash) ON DELETE CASCADE,
    wallet_id INTEGER NOT NULL REFERENCES t_wallet(wallet_id) ON DELETE CASCADE,
    io_type TEXT NOT NULL CHECK (io_type IN ('input','output')),
    address TEXT NOT NULL, -- the wallet address matched
    -- ADA value (lovelace). When NULL, row represents a token transfer only
    lovelace BIGINT,
    -- Token fields (nullable for ADA-only rows)
    policy_id TEXT,
    asset_name_hex TEXT,
    token_value_raw NUMERIC(40,0), -- integer raw quantity from chain
    token_amount NUMERIC(36,8),    -- formatted amount after decimals (if known)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cardano_io_wallet ON t_cardano_tx_io(wallet_id);
CREATE INDEX IF NOT EXISTS idx_cardano_io_tx ON t_cardano_tx_io(tx_hash);
CREATE INDEX IF NOT EXISTS idx_cardano_io_asset ON t_cardano_tx_io(policy_id, asset_name_hex);

-- Sync state per wallet to enable incremental sync
CREATE TABLE IF NOT EXISTS t_cardano_sync_state (
    wallet_id INTEGER PRIMARY KEY REFERENCES t_wallet(wallet_id) ON DELETE CASCADE,
    last_block_height INTEGER,
    last_tx_timestamp TIMESTAMP WITH TIME ZONE,
    last_synced_at TIMESTAMP WITH TIME ZONE
);

-- Helpful view: net daily deltas (by asset policy/name) for a wallet
CREATE OR REPLACE VIEW v_cardano_daily_deltas AS
WITH io AS (
    SELECT 
        t.tx_timestamp::date AS dt,
        i.wallet_id,
        i.policy_id,
        i.asset_name_hex,
        -- ADA: use lovelace (converted later in app); Tokens: use token_value_raw
        SUM(CASE WHEN i.io_type = 'output' THEN COALESCE(i.lovelace, 0) ELSE -COALESCE(i.lovelace, 0) END) AS net_lovelace,
        SUM(CASE WHEN i.io_type = 'output' THEN COALESCE(i.token_value_raw, 0) ELSE -COALESCE(i.token_value_raw, 0) END) AS net_token_raw
    FROM t_cardano_tx_io i
    JOIN t_cardano_transactions t ON t.tx_hash = i.tx_hash
    GROUP BY 1,2,3,4
)
SELECT * FROM io;

-- Comments for documentation
COMMENT ON TABLE t_cardano_transactions IS 'Raw Cardano transactions per tracked wallet (one row per tx).';
COMMENT ON TABLE t_cardano_tx_io IS 'Per-IO breakdown for tracked wallet address; ADA in lovelace, tokens by policy/asset_name.';
COMMENT ON TABLE t_cardano_assets IS 'Resolved metadata for Cardano native tokens (name/decimals).';
COMMENT ON TABLE t_cardano_sync_state IS 'Incremental sync state for Cardano wallets.';
