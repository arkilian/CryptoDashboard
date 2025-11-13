-- ========================================
-- CRYPTO DASHBOARD - SCHEMA DA BASE DE DADOS
-- ========================================
-- Esquema completo para criar uma base de dados nova
-- já com o Modelo de Transações V2 (multi-asset, multi-conta).
-- 
-- INSTRUÇÕES DE USO:
-- 1. Criar base de dados: CREATE DATABASE crypto_dashboard;
-- 2. Aplicar schema: psql -U <user> -d crypto_dashboard -f schema.sql
-- 3. Importar dados: psql -U <user> -d crypto_dashboard -f data_export.sql
-- ========================================

-- ========================================
-- TABELAS DE UTILIZADORES E PERFIS
-- ========================================

CREATE TABLE IF NOT EXISTS t_users (
    user_id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS t_gender (
    gender_id SERIAL PRIMARY KEY,
    gender_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS t_address (
    address_id SERIAL PRIMARY KEY,
    street TEXT,
    city TEXT,
    postal_code TEXT,
    country TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS t_user_profile (
    profile_id SERIAL PRIMARY KEY,
    user_id INT UNIQUE REFERENCES t_users(user_id) ON DELETE CASCADE,
    email TEXT,
    first_name TEXT,
    last_name TEXT,
    birth_date DATE,
    gender_id INT REFERENCES t_gender(gender_id),
    address_id INT REFERENCES t_address(address_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- TABELAS DE TAXAS E CONFIGURAÇÕES
-- ========================================

CREATE TABLE IF NOT EXISTS t_fee_settings (
    setting_id SERIAL PRIMARY KEY,
    maintenance_rate NUMERIC(6,4) NOT NULL DEFAULT 0.0025,
    maintenance_min NUMERIC(10,2) NOT NULL DEFAULT 3.00,
    performance_rate NUMERIC(6,4) NOT NULL DEFAULT 0.10,
    valid_from TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS t_user_high_water (
    user_id INT PRIMARY KEY REFERENCES t_users(user_id),
    high_water_value NUMERIC(18,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS t_user_fees (
    fee_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES t_users(user_id),
    fee_type TEXT CHECK (fee_type IN ('maintenance','performance')),
    amount NUMERIC(18,2) NOT NULL,
    fee_date DATE NOT NULL
);

-- ========================================
-- TABELAS DE EXCHANGES, ATIVOS E CONTAS
-- ========================================

CREATE TABLE IF NOT EXISTS t_exchanges (
    exchange_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT
);

CREATE TABLE IF NOT EXISTS t_assets (
    asset_id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL UNIQUE,
    name TEXT,
    chain TEXT,
    coingecko_id TEXT,
    is_stablecoin BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS t_exchange_accounts (
    account_id SERIAL PRIMARY KEY,
    exchange_id INTEGER REFERENCES t_exchanges(exchange_id),
    user_id INTEGER REFERENCES t_users(user_id),
    name TEXT,
    account_category TEXT
);

-- ========================================
-- MOVIMENTOS DE CAPITAL DOS UTILIZADORES
-- ========================================

CREATE TABLE IF NOT EXISTS t_user_capital_movements (
    movement_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES t_users(user_id) ON DELETE CASCADE,
    movement_date DATE NOT NULL DEFAULT CURRENT_DATE,
    credit NUMERIC(18,2) DEFAULT 0,
    debit NUMERIC(18,2) DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- TRANSACOES (MODELO V2)
-- ========================================

CREATE TABLE IF NOT EXISTS t_transactions (
    transaction_id SERIAL PRIMARY KEY,
    transaction_type TEXT NOT NULL CHECK (transaction_type IN (
        'buy','sell',
        'deposit','withdrawal',
        'swap','transfer',
        'stake','unstake','reward',
        'lend','borrow','repay','liquidate'
    )),
    -- Campos legacy (mantidos para compatibilidade)
    asset_id INT REFERENCES t_assets(asset_id),
    quantity NUMERIC(36,8),
    price_eur NUMERIC(18,6),
    total_eur NUMERIC(18,2),
    fee_eur NUMERIC(18,2) DEFAULT 0,
    exchange_id INT REFERENCES t_exchanges(exchange_id),
    account_id INT REFERENCES t_exchange_accounts(account_id),
    -- Campos V2 (multi-asset/multi-account)
    from_asset_id INT REFERENCES t_assets(asset_id),
    to_asset_id INT REFERENCES t_assets(asset_id),
    from_quantity NUMERIC(36,8),
    to_quantity NUMERIC(36,8),
    from_account_id INT REFERENCES t_exchange_accounts(account_id),
    to_account_id INT REFERENCES t_exchange_accounts(account_id),
    fee_asset_id INT REFERENCES t_assets(asset_id),
    fee_quantity NUMERIC(36,8) DEFAULT 0,
    -- Metadados
    transaction_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    executed_by INT REFERENCES t_users(user_id),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- TABELAS DE SNAPSHOTS DE PREÇOS
-- ========================================

CREATE TABLE IF NOT EXISTS t_price_snapshots (
    snapshot_id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL REFERENCES t_assets(asset_id),
    snapshot_date DATE NOT NULL,
    price_eur NUMERIC(18, 6) NOT NULL,
    source TEXT DEFAULT 'coingecko',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(asset_id, snapshot_date)
);

CREATE TABLE IF NOT EXISTS t_portfolio_snapshots (
    snapshot_id SERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    total_value NUMERIC(18,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS t_portfolio_holdings (
    holding_id SERIAL PRIMARY KEY,
    snapshot_id INT REFERENCES t_portfolio_snapshots(snapshot_id) ON DELETE CASCADE,
    asset_symbol TEXT NOT NULL,
    quantity NUMERIC(18,6) NOT NULL,
    price NUMERIC(18,6) NOT NULL,
    valor_total NUMERIC(18,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS t_user_snapshots (
    user_snapshot_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES t_users(user_id),
    snapshot_date DATE NOT NULL,
    valor_antes NUMERIC(18,2),
    valor_depois NUMERIC(18,2)
);

CREATE TABLE IF NOT EXISTS t_user_manual_snapshots (
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

CREATE TABLE IF NOT EXISTS t_snapshot_assets (
    id SERIAL PRIMARY KEY,
    snapshot_id INTEGER REFERENCES t_user_manual_snapshots(snapshot_id),
    account_id INTEGER REFERENCES t_exchange_accounts(account_id),
    asset_id INTEGER REFERENCES t_assets(asset_id),
    amount NUMERIC(36, 8),
    price_eur NUMERIC(18, 6),
    value_eur NUMERIC(18, 6) GENERATED ALWAYS AS (amount * price_eur) STORED
);

-- ========================================
-- TAGS E RELACAO N:N COM TRANSACOES
-- ========================================

CREATE TABLE IF NOT EXISTS t_tags (
    tag_id SERIAL PRIMARY KEY,
    tag_code TEXT UNIQUE NOT NULL,
    tag_label TEXT,
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS t_transaction_tags (
    transaction_id INTEGER NOT NULL REFERENCES t_transactions(transaction_id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES t_tags(tag_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(transaction_id, tag_id)
);

-- ========================================
-- SISTEMA DE SHARES (OWNERSHIP)
-- ========================================

CREATE TABLE IF NOT EXISTS t_user_shares (
    share_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES t_users(user_id),
    movement_date TIMESTAMP WITH TIME ZONE NOT NULL,
    movement_type VARCHAR(20) NOT NULL,
    amount_eur NUMERIC(18, 2) NOT NULL,
    nav_per_share NUMERIC(18, 6) NOT NULL,
    shares_amount NUMERIC(18, 6) NOT NULL,
    total_shares_after NUMERIC(18, 6) NOT NULL,
    fund_nav NUMERIC(18, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- ========================================
-- TABELAS WALLET E BANCO
-- ========================================

CREATE TABLE IF NOT EXISTS t_wallet (
    wallet_id SERIAL PRIMARY KEY,
    wallet_name TEXT NOT NULL,
    wallet_address TEXT UNIQUE NOT NULL,
    blockchain TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS t_banco (
    bank_id SERIAL PRIMARY KEY,
    bank_name TEXT NOT NULL,
    account_number TEXT,
    swift_code TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- CONFIGURACOES DE API
-- ========================================

CREATE TABLE IF NOT EXISTS t_api_coingecko (
    api_id SERIAL PRIMARY KEY,
    api_key TEXT,
    rate_limit_per_minute INTEGER DEFAULT 10,
    last_request_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS t_api_cardano (
    api_id SERIAL PRIMARY KEY,
    wallet_id INTEGER REFERENCES t_wallet(wallet_id),
    api_key TEXT,
    api_endpoint TEXT DEFAULT 'https://api.cardanoscan.io/api/v1',
    rate_limit_per_minute INTEGER DEFAULT 60,
    last_request_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- TABELAS CARDANO
-- ========================================

CREATE TABLE IF NOT EXISTS t_cardano_assets (
    asset_id SERIAL PRIMARY KEY,
    policy_id TEXT NOT NULL,
    asset_name TEXT NOT NULL,
    fingerprint TEXT UNIQUE,
    display_name TEXT,
    decimals INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(policy_id, asset_name)
);

CREATE TABLE IF NOT EXISTS t_cardano_transactions (
    cardano_tx_id SERIAL PRIMARY KEY,
    wallet_id INTEGER REFERENCES t_wallet(wallet_id),
    tx_hash TEXT NOT NULL,
    block_time TIMESTAMP WITH TIME ZONE NOT NULL,
    block_height INTEGER,
    fee BIGINT NOT NULL,
    tx_type TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tx_hash)
);

CREATE TABLE IF NOT EXISTS t_cardano_tx_io (
    io_id SERIAL PRIMARY KEY,
    cardano_tx_id INTEGER REFERENCES t_cardano_transactions(cardano_tx_id) ON DELETE CASCADE,
    io_type TEXT NOT NULL CHECK (io_type IN ('input', 'output')),
    address TEXT NOT NULL,
    ada_amount BIGINT NOT NULL,
    asset_policy_id TEXT,
    asset_name TEXT,
    asset_quantity BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- VIEW: SHARES ATUAIS POR UTILIZADOR
-- ========================================

CREATE OR REPLACE VIEW v_user_current_shares AS
SELECT 
    user_id,
    SUM(shares_amount) as total_shares
FROM t_user_shares
GROUP BY user_id
HAVING SUM(shares_amount) > 0;

-- ========================================
-- ÍNDICES
-- ========================================

-- Utilizadores
CREATE INDEX IF NOT EXISTS idx_users_username ON t_users(username);
CREATE INDEX IF NOT EXISTS idx_user_profile_user_id ON t_user_profile(user_id);

-- Movimentos de capital
CREATE INDEX IF NOT EXISTS idx_capital_movements_user_id ON t_user_capital_movements(user_id);
CREATE INDEX IF NOT EXISTS idx_capital_movements_date ON t_user_capital_movements(movement_date);

-- Transações
CREATE INDEX IF NOT EXISTS idx_transactions_date ON t_transactions(transaction_date DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON t_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_transactions_executed_by ON t_transactions(executed_by);
CREATE INDEX IF NOT EXISTS idx_transactions_account ON t_transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_from_asset ON t_transactions(from_asset_id);
CREATE INDEX IF NOT EXISTS idx_transactions_to_asset ON t_transactions(to_asset_id);
CREATE INDEX IF NOT EXISTS idx_transactions_from_account ON t_transactions(from_account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_to_account ON t_transactions(to_account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_fee_asset ON t_transactions(fee_asset_id);

-- Preços
CREATE INDEX IF NOT EXISTS idx_price_snapshots_asset_date ON t_price_snapshots(asset_id, snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_price_snapshots_date ON t_price_snapshots(snapshot_date DESC);

-- Snapshots
CREATE INDEX IF NOT EXISTS idx_user_snapshots_user_date ON t_user_snapshots(user_id, snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_user_manual_snapshots_user_date ON t_user_manual_snapshots(user_id, snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_date ON t_portfolio_snapshots(snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_portfolio_holdings_snapshot ON t_portfolio_holdings(snapshot_id);

-- Taxas
CREATE INDEX IF NOT EXISTS idx_user_fees_user_date ON t_user_fees(user_id, fee_date DESC);
CREATE INDEX IF NOT EXISTS idx_user_fees_user_type_date ON t_user_fees(user_id, fee_type, fee_date);
CREATE INDEX IF NOT EXISTS idx_user_high_water_user ON t_user_high_water(user_id);
CREATE INDEX IF NOT EXISTS idx_fee_settings_valid_from ON t_fee_settings(valid_from DESC);

-- Shares
CREATE INDEX IF NOT EXISTS idx_user_shares_user_date ON t_user_shares(user_id, movement_date DESC);
CREATE INDEX IF NOT EXISTS idx_user_shares_date ON t_user_shares(movement_date DESC);

-- Cardano
CREATE INDEX IF NOT EXISTS idx_cardano_transactions_wallet ON t_cardano_transactions(wallet_id);
CREATE INDEX IF NOT EXISTS idx_cardano_transactions_hash ON t_cardano_transactions(tx_hash);
CREATE INDEX IF NOT EXISTS idx_cardano_transactions_block_time ON t_cardano_transactions(block_time DESC);
CREATE INDEX IF NOT EXISTS idx_cardano_tx_io_tx ON t_cardano_tx_io(cardano_tx_id);
CREATE INDEX IF NOT EXISTS idx_cardano_tx_io_address ON t_cardano_tx_io(address);
CREATE INDEX IF NOT EXISTS idx_cardano_assets_fingerprint ON t_cardano_assets(fingerprint);
CREATE INDEX IF NOT EXISTS idx_cardano_assets_policy ON t_cardano_assets(policy_id, asset_name);

-- ========================================
-- FIM DO SCHEMA
-- ========================================
