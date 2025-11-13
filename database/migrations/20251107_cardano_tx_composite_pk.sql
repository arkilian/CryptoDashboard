-- ========================================
-- MIGRATION: Change Cardano TX primary key to composite
-- Date: 2025-11-07
-- Allows same transaction to appear multiple times when involving multiple user wallets.
-- Example: Transfer from Wallet2→Wallet1 should appear in BOTH wallets with different perspectives.
-- ========================================

-- Step 0: Duplicate cross-wallet transactions
-- Find transactions where IO belongs to different wallet than TX record
INSERT INTO t_cardano_transactions (tx_hash, wallet_id, address, block_height, tx_timestamp, status, fees_ada, raw_payload)
SELECT DISTINCT
    t.tx_hash,
    io.wallet_id as target_wallet,
    w.address as target_address,
    t.block_height,
    t.tx_timestamp,
    t.status,
    t.fees_ada,
    t.raw_payload
FROM t_cardano_transactions t
JOIN t_cardano_tx_io io ON io.tx_hash = t.tx_hash
JOIN t_wallet w ON w.wallet_id = io.wallet_id
WHERE io.wallet_id != t.wallet_id
ON CONFLICT (tx_hash) DO NOTHING;

-- At this point, some transactions still won't be duplicated due to PK conflict
-- We'll handle this after removing the PK

-- Step 1: Drop foreign key constraints that reference tx_hash
ALTER TABLE IF EXISTS t_cardano_tx_io
DROP CONSTRAINT IF EXISTS t_cardano_tx_io_tx_hash_fkey;

-- Step 2: Drop the old primary key
ALTER TABLE t_cardano_transactions
DROP CONSTRAINT IF EXISTS t_cardano_transactions_pkey;

-- Step 3: NOW duplicate the blocked transactions (they can finally be inserted)
INSERT INTO t_cardano_transactions (tx_hash, wallet_id, address, block_height, tx_timestamp, status, fees_ada, raw_payload)
SELECT DISTINCT
    t.tx_hash,
    io.wallet_id as target_wallet,
    w.address as target_address,
    t.block_height,
    t.tx_timestamp,
    t.status,
    t.fees_ada,
    t.raw_payload
FROM t_cardano_transactions t
JOIN t_cardano_tx_io io ON io.tx_hash = t.tx_hash
JOIN t_wallet w ON w.wallet_id = io.wallet_id
WHERE io.wallet_id != t.wallet_id
  AND NOT EXISTS (
    SELECT 1 FROM t_cardano_transactions t2
    WHERE t2.tx_hash = t.tx_hash AND t2.wallet_id = io.wallet_id
  );

-- Step 4: Add composite primary key
ALTER TABLE t_cardano_transactions
ADD CONSTRAINT t_cardano_transactions_pkey PRIMARY KEY (tx_hash, wallet_id);

-- Step 5: Recreate foreign key (now references composite key)
ALTER TABLE t_cardano_tx_io
ADD CONSTRAINT t_cardano_tx_io_tx_fkey 
FOREIGN KEY (tx_hash, wallet_id) 
REFERENCES t_cardano_transactions(tx_hash, wallet_id) 
ON DELETE CASCADE;

-- Step 6: Update comment
COMMENT ON TABLE t_cardano_transactions IS 
'Raw Cardano transactions per tracked wallet. Same tx_hash can appear multiple times for different wallets (e.g., inter-wallet transfers).';
