-- ========================================
-- CRYPTO DASHBOARD - DATABASE SCHEMA
-- ========================================
-- Este ficheiro contém todas as tabelas necessárias para criar
-- uma base de dados nova do zero, incluindo:
-- - Gestão de utilizadores e perfis
-- - Snapshots de portfolio e ativos
-- - Taxas e high water marks
-- - Movimentos de capital
-- - Exchanges e contas
-- ========================================

-- ========================================
-- TABELAS DE UTILIZADORES
-- ========================================

-- Users
CREATE TABLE IF NOT EXISTS t_users (
    user_id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE
);

-- Gender lookup table
CREATE TABLE IF NOT EXISTS t_gender (
    gender_id SERIAL PRIMARY KEY,
    gender_name TEXT UNIQUE NOT NULL
);

-- Address table
CREATE TABLE IF NOT EXISTS t_address (
    address_id SERIAL PRIMARY KEY,
    street TEXT,
    city TEXT,
    postal_code TEXT,
    country TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User profile table (extends t_users)
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

-- Fee Settings (com histórico)
CREATE TABLE IF NOT EXISTS t_fee_settings (
    setting_id SERIAL PRIMARY KEY,
    maintenance_rate NUMERIC(6,4) NOT NULL DEFAULT 0.0025,
    maintenance_min NUMERIC(10,2) NOT NULL DEFAULT 3.00,
    performance_rate NUMERIC(6,4) NOT NULL DEFAULT 0.10,
    valid_from TIMESTAMP NOT NULL DEFAULT NOW()
);

-- High Water Mark
CREATE TABLE IF NOT EXISTS t_user_high_water (
    user_id INT PRIMARY KEY REFERENCES t_users(user_id),
    high_water_value NUMERIC(18,2) NOT NULL
);

-- Histórico de taxas aplicadas
CREATE TABLE IF NOT EXISTS t_user_fees (
    fee_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES t_users(user_id),
    fee_type TEXT CHECK (fee_type IN ('maintenance','performance')),
    amount NUMERIC(18,2) NOT NULL,
    fee_date DATE NOT NULL
);

-- ========================================
-- TABELAS DE PORTFOLIO E SNAPSHOTS
-- ========================================

-- Snapshots do fundo
CREATE TABLE IF NOT EXISTS t_portfolio_snapshots (
    snapshot_id SERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    total_value NUMERIC(18,2) NOT NULL
);

-- Holdings de cada snapshot
CREATE TABLE IF NOT EXISTS t_portfolio_holdings (
    holding_id SERIAL PRIMARY KEY,
    snapshot_id INT REFERENCES t_portfolio_snapshots(snapshot_id) ON DELETE CASCADE,
    asset_symbol TEXT NOT NULL,
    quantity NUMERIC(18,6) NOT NULL,
    price NUMERIC(18,6) NOT NULL,
    valor_total NUMERIC(18,2) NOT NULL
);

-- Snapshots de cada utilizador
CREATE TABLE IF NOT EXISTS t_user_snapshots (
    user_snapshot_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES t_users(user_id),
    snapshot_date DATE NOT NULL,
    valor_antes NUMERIC(18,2),
    valor_depois NUMERIC(18,2)
);

-- Manual snapshots for tracking user assets across different wallets
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

-- ========================================
-- TABELAS DE MOVIMENTOS E CAPITAL
-- ========================================

-- User capital movements (deposits, withdrawals, etc.)
CREATE TABLE IF NOT EXISTS t_user_capital_movements (
    movement_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES t_users(user_id) ON DELETE CASCADE,
    movement_date DATE NOT NULL DEFAULT CURRENT_DATE,
    credit NUMERIC(18,2) DEFAULT 0,
    debit NUMERIC(18,2) DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Portfolio transactions (admin buy/sell operations)
CREATE TABLE IF NOT EXISTS t_transactions (
    transaction_id SERIAL PRIMARY KEY,
    transaction_type TEXT CHECK (transaction_type IN ('buy', 'sell')) NOT NULL,
    asset_id INT REFERENCES t_assets(asset_id) NOT NULL,
    quantity NUMERIC(36,8) NOT NULL,
    price_eur NUMERIC(18,6) NOT NULL,
    total_eur NUMERIC(18,2) NOT NULL,
    fee_eur NUMERIC(18,2) DEFAULT 0,
    exchange_id INT REFERENCES t_exchanges(exchange_id),
    transaction_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    executed_by INT REFERENCES t_users(user_id),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- TABELAS DE EXCHANGES E ATIVOS
-- ========================================

CREATE TABLE IF NOT EXISTS t_exchanges (
    exchange_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,              -- Ex: Binance, Ledger, Minswap
    category TEXT                    -- Ex: CEX, Wallet, DeFi
);

CREATE TABLE IF NOT EXISTS t_assets (
    asset_id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL UNIQUE,     -- Ex: BTC, ADA, DJED
    name TEXT,
    chain TEXT,                      -- Ex: Bitcoin, Cardano, Solana
    coingecko_id TEXT,               -- ID do ativo no CoinGecko (ex: bitcoin, cardano)
    is_stablecoin BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS t_exchange_accounts (
    account_id SERIAL PRIMARY KEY,
    exchange_id INTEGER REFERENCES t_exchanges(exchange_id),
    user_id INTEGER REFERENCES t_users(user_id),
    name TEXT                        -- Ex: "Futuros", "Earn", "Bot 1"
);

CREATE TABLE IF NOT EXISTS t_user_payment_methods (
    method_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES t_users(user_id),
    method_type VARCHAR(50), -- exemplo: 'IBAN', 'Wallet', 'PayPal'
    label VARCHAR(100),      -- exemplo: 'Conta principal', 'Ledger Wallet'
    details TEXT             -- IBAN ou endereço de wallet
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
-- ÍNDICES PARA PERFORMANCE
-- ========================================

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

-- Index on t_user_high_water for faster high water mark queries
CREATE INDEX IF NOT EXISTS idx_user_high_water_user ON t_user_high_water(user_id);

-- Index on t_fee_settings for faster configuration lookups
CREATE INDEX IF NOT EXISTS idx_fee_settings_valid_from ON t_fee_settings(valid_from DESC);

-- Index for t_user_profile
CREATE INDEX IF NOT EXISTS idx_user_profile_user_id ON t_user_profile(user_id);

-- Indexes for t_user_capital_movements
CREATE INDEX IF NOT EXISTS idx_capital_movements_user_id ON t_user_capital_movements(user_id);
CREATE INDEX IF NOT EXISTS idx_capital_movements_date ON t_user_capital_movements(movement_date);

-- Indexes for t_transactions
CREATE INDEX IF NOT EXISTS idx_transactions_date ON t_transactions(transaction_date DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_asset ON t_transactions(asset_id);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON t_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_transactions_executed_by ON t_transactions(executed_by);

-- ========================================
-- DADOS INICIAIS
-- ========================================

-- Inserir opções de género
INSERT INTO t_gender (gender_name) VALUES 
    ('Masculino'),
    ('Feminino'),
    ('Outro'),
    ('Prefiro não dizer')
ON CONFLICT (gender_name) DO NOTHING;

-- Inserir taxas iniciais
INSERT INTO t_fee_settings (maintenance_rate, maintenance_min, performance_rate)
VALUES (0.0025, 3.00, 0.10)
ON CONFLICT DO NOTHING;

-- Inserir utilizador admin (password: cryptodashboard)
-- Hash gerado com bcrypt para a password "cryptodashboard"
-- modificar password no primeiro login
INSERT INTO t_users (username, password_hash, salt, is_admin)
VALUES ('admin', '$2b$12$oMxa6Y.vTnhWFrDQGQxmveSXab5FeKihuoLSb3W0FdnkPJaV9HFoS', '', TRUE)
ON CONFLICT (username) DO NOTHING;

-- Inserir exchanges comuns
INSERT INTO t_exchanges (name, category) VALUES 
    ('Binance', 'CEX'),
    ('Kraken', 'CEX'),
    ('Coinbase', 'CEX'),
    ('Ledger', 'Wallet'),
    ('Minswap', 'DeFi'),
    ('SundaeSwap', 'DeFi')
ON CONFLICT DO NOTHING;

-- Inserir ativos comuns
INSERT INTO t_assets (symbol, name, chain, coingecko_id, is_stablecoin) VALUES 
    ('BTC', 'Bitcoin', 'Bitcoin', 'bitcoin', FALSE),
    ('ETH', 'Ethereum', 'Ethereum', 'ethereum', FALSE),
    ('ADA', 'Cardano', 'Cardano', 'cardano', FALSE),
    ('SOL', 'Solana', 'Solana', 'solana', FALSE),
    ('USDT', 'Tether', 'Multiple', 'tether', TRUE),
    ('USDC', 'USD Coin', 'Multiple', 'usd-coin', TRUE),
    ('DJED', 'Djed', 'Cardano', 'djed', TRUE),
    ('SHEN', 'Shen', 'Cardano', 'shen', FALSE)
ON CONFLICT (symbol) DO NOTHING;

