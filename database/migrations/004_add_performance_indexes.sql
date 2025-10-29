-- Migration 004: Add performance indexes for commonly queried columns
-- This migration adds indexes to improve query performance across the application

-- Index on t_users.username for faster login lookups
CREATE INDEX IF NOT EXISTS idx_users_username ON t_users(username);

-- Index on t_user_snapshots for faster snapshot queries
CREATE INDEX IF NOT EXISTS idx_user_snapshots_user_date ON t_user_snapshots(user_id, snapshot_date DESC);

-- Index on t_user_manual_snapshots for faster user snapshot lookups
CREATE INDEX IF NOT EXISTS idx_user_manual_snapshots_user_date ON t_user_manual_snapshots(user_id, snapshot_date DESC);

-- Index on t_user_fees for faster fee history queries
CREATE INDEX IF NOT EXISTS idx_user_fees_user_date ON t_user_fees(user_id, fee_date DESC);
CREATE INDEX IF NOT EXISTS idx_user_fees_user_type_date ON t_user_fees(user_id, fee_type, fee_date);

-- Index on t_portfolio_snapshots for faster portfolio queries
CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_date ON t_portfolio_snapshots(snapshot_date DESC);

-- Index on t_portfolio_holdings for faster asset lookups
CREATE INDEX IF NOT EXISTS idx_portfolio_holdings_snapshot ON t_portfolio_holdings(snapshot_id);

-- Index on t_user_high_water for faster high water mark queries (if table exists)
-- This table is referenced in fees.py
CREATE INDEX IF NOT EXISTS idx_user_high_water_user ON t_user_high_water(user_id);

-- Index on t_fee_settings for faster configuration lookups
CREATE INDEX IF NOT EXISTS idx_fee_settings_valid_from ON t_fee_settings(valid_from DESC);
