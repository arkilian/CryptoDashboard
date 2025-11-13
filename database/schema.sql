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
    user_id INTEGER REFERENCES t_users(user_id),
    wallet_name TEXT NOT NULL,
    wallet_type TEXT,
    blockchain TEXT NOT NULL,
    address TEXT UNIQUE NOT NULL,
    stake_address TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_primary BOOLEAN DEFAULT FALSE,
    balance_last_sync TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS t_banco (
    banco_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES t_users(user_id),
    bank_name TEXT NOT NULL,
    account_holder TEXT,
    iban TEXT,
    swift_bic TEXT,
    account_number TEXT,
    currency TEXT DEFAULT 'EUR',
    country TEXT,
    branch TEXT,
    account_type TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_primary BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- CONFIGURACOES DE API
-- ========================================

CREATE TABLE IF NOT EXISTS t_api_coingecko (
    api_id SERIAL PRIMARY KEY,
    api_name TEXT,
    api_key TEXT,
    base_url TEXT,
    rate_limit INTEGER,
    rate_limit_per_minute INTEGER DEFAULT 10,
    timeout INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    last_request_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS t_api_cardano (
    api_id SERIAL PRIMARY KEY,
    api_name TEXT,
    wallet_id INTEGER REFERENCES t_wallet(wallet_id),
    api_key TEXT,
    base_url TEXT,
    default_address TEXT,
    api_endpoint TEXT DEFAULT 'https://api.cardanoscan.io/api/v1',
    rate_limit INTEGER,
    rate_limit_per_minute INTEGER DEFAULT 60,
    timeout INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    last_request_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- TABELAS CARDANO
-- ========================================

CREATE TABLE IF NOT EXISTS t_cardano_assets (
    policy_id TEXT NOT NULL,
    asset_name_hex TEXT,
    display_name TEXT,
    decimals INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_cardano_assets PRIMARY KEY (policy_id, asset_name_hex)
);

CREATE TABLE IF NOT EXISTS t_cardano_transactions (
    tx_hash TEXT NOT NULL,
    wallet_id INTEGER NOT NULL REFERENCES t_wallet(wallet_id) ON DELETE CASCADE,
    address TEXT NOT NULL,
    block_height INTEGER,
    tx_timestamp TIMESTAMP WITH TIME ZONE,
    status TEXT,
    fees_ada NUMERIC(36, 8) DEFAULT 0,
    raw_payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT t_cardano_transactions_pkey PRIMARY KEY (tx_hash, wallet_id)
);

CREATE TABLE IF NOT EXISTS t_cardano_tx_io (
    io_id BIGSERIAL PRIMARY KEY,
    tx_hash TEXT NOT NULL,
    wallet_id INTEGER NOT NULL REFERENCES t_wallet(wallet_id) ON DELETE CASCADE,
    io_type TEXT NOT NULL CHECK (io_type IN ('input', 'output')),
    address TEXT NOT NULL,
    lovelace BIGINT,
    policy_id TEXT,
    asset_name_hex TEXT,
    token_value_raw NUMERIC(40, 0),
    token_amount NUMERIC(36, 8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT t_cardano_tx_io_tx_fkey 
        FOREIGN KEY (tx_hash, wallet_id) 
        REFERENCES t_cardano_transactions(tx_hash, wallet_id) 
        ON DELETE CASCADE
);

-- ========================================
-- SYNC STATE PER WALLET
-- ========================================

CREATE TABLE IF NOT EXISTS t_cardano_sync_state (
    wallet_id INTEGER PRIMARY KEY REFERENCES t_wallet(wallet_id) ON DELETE CASCADE,
    last_block_height INTEGER,
    last_tx_timestamp TIMESTAMP WITH TIME ZONE,
    last_synced_at TIMESTAMP WITH TIME ZONE
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
-- VIEWS ÚTEIS - WALLETS E BANCOS
-- ========================================

CREATE OR REPLACE VIEW v_user_active_wallets AS
SELECT 
    w.wallet_id,
    w.user_id,
    u.username,
    w.wallet_name,
    w.wallet_type,
    w.blockchain,
    w.address,
    w.stake_address,
    w.is_primary,
    w.balance_last_sync
FROM t_wallet w
JOIN t_users u ON w.user_id = u.user_id
WHERE w.is_active = TRUE
ORDER BY u.username, w.is_primary DESC, w.wallet_name;

CREATE OR REPLACE VIEW v_user_active_banks AS
SELECT 
    b.banco_id,
    b.user_id,
    u.username,
    b.bank_name,
    b.account_holder,
    b.iban,
    b.swift_bic,
    b.currency,
    b.is_primary
FROM t_banco b
JOIN t_users u ON b.user_id = u.user_id
WHERE b.is_active = TRUE
ORDER BY u.username, b.is_primary DESC, b.bank_name;

CREATE OR REPLACE VIEW v_active_apis AS
SELECT 
    api_id,
    api_name,
    base_url,
    rate_limit,
    timeout,
    created_at,
    updated_at
FROM t_api_cardano
WHERE is_active = TRUE
ORDER BY api_name;

-- ========================================
-- VIEW: CARDANO DAILY DELTAS
-- ========================================

CREATE OR REPLACE VIEW v_cardano_daily_deltas AS
WITH io AS (
    SELECT 
        t.tx_timestamp::date AS dt,
        i.wallet_id,
        i.policy_id,
        i.asset_name_hex,
        SUM(CASE WHEN i.io_type = 'output' THEN COALESCE(i.lovelace, 0) ELSE -COALESCE(i.lovelace, 0) END) AS net_lovelace,
        SUM(CASE WHEN i.io_type = 'output' THEN COALESCE(i.token_value_raw, 0) ELSE -COALESCE(i.token_value_raw, 0) END) AS net_token_raw
    FROM t_cardano_tx_io i
    JOIN t_cardano_transactions t ON t.tx_hash = i.tx_hash AND t.wallet_id = i.wallet_id
    GROUP BY 1,2,3,4
)
SELECT * FROM io;

-- ========================================
-- TRIGGERS E FUNÇÕES
-- ========================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_wallet_updated_at ON t_wallet;
CREATE TRIGGER update_wallet_updated_at
    BEFORE UPDATE ON t_wallet
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_banco_updated_at ON t_banco;
CREATE TRIGGER update_banco_updated_at
    BEFORE UPDATE ON t_banco
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_api_cardano_updated_at ON t_api_cardano;
CREATE TRIGGER update_api_cardano_updated_at
    BEFORE UPDATE ON t_api_cardano
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_api_coingecko_updated_at ON t_api_coingecko;
CREATE TRIGGER update_api_coingecko_updated_at
    BEFORE UPDATE ON t_api_coingecko
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

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
CREATE INDEX IF NOT EXISTS idx_cardano_transactions_address ON t_cardano_transactions(address);
CREATE INDEX IF NOT EXISTS idx_cardano_transactions_tx_timestamp ON t_cardano_transactions(tx_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_cardano_transactions_status ON t_cardano_transactions(status);
CREATE INDEX IF NOT EXISTS idx_cardano_tx_io_tx_wallet ON t_cardano_tx_io(tx_hash, wallet_id);
CREATE INDEX IF NOT EXISTS idx_cardano_tx_io_wallet ON t_cardano_tx_io(wallet_id);
CREATE INDEX IF NOT EXISTS idx_cardano_tx_io_tx_hash ON t_cardano_tx_io(tx_hash);
CREATE INDEX IF NOT EXISTS idx_cardano_tx_io_address ON t_cardano_tx_io(address);
CREATE INDEX IF NOT EXISTS idx_cardano_tx_io_policy ON t_cardano_tx_io(policy_id);
CREATE INDEX IF NOT EXISTS idx_cardano_assets_policy ON t_cardano_assets(policy_id, asset_name_hex);

-- API Config
CREATE INDEX IF NOT EXISTS idx_api_coingecko_active ON t_api_coingecko(is_active);
CREATE INDEX IF NOT EXISTS idx_api_cardano_wallet ON t_api_cardano(wallet_id);
CREATE INDEX IF NOT EXISTS idx_api_cardano_active ON t_api_cardano(is_active);

-- Wallet e Banco
CREATE INDEX IF NOT EXISTS idx_wallet_user_id ON t_wallet(user_id);
CREATE INDEX IF NOT EXISTS idx_wallet_address ON t_wallet(address);
CREATE INDEX IF NOT EXISTS idx_wallet_blockchain ON t_wallet(blockchain);
CREATE INDEX IF NOT EXISTS idx_wallet_active ON t_wallet(is_active);
CREATE INDEX IF NOT EXISTS idx_banco_user_id ON t_banco(user_id);
CREATE INDEX IF NOT EXISTS idx_banco_iban ON t_banco(iban);
CREATE INDEX IF NOT EXISTS idx_banco_active ON t_banco(is_active);

-- ========================================
-- COMENTÁRIOS NAS TABELAS (DOCUMENTAÇÃO)
-- ========================================

-- Utilizadores
COMMENT ON TABLE t_users IS 'Utilizadores do sistema com autenticação bcrypt';
COMMENT ON TABLE t_user_profile IS 'Perfis detalhados dos utilizadores (informação pessoal)';

-- APIs
COMMENT ON TABLE t_api_cardano IS 'Configurações de APIs para consultas blockchain (inicialmente Cardano)';
COMMENT ON TABLE t_api_coingecko IS 'Configurações de API do CoinGecko para preços de criptomoedas';
COMMENT ON COLUMN t_api_cardano.api_key IS 'Chave de API (sensível - deve ser encriptada)';
COMMENT ON COLUMN t_api_cardano.default_address IS 'Endereço padrão usado nas consultas';
COMMENT ON COLUMN t_api_cardano.rate_limit IS 'Limite de requests por minuto';

-- Wallets e Bancos
COMMENT ON TABLE t_wallet IS 'Gestão de wallets dos utilizadores (hot, cold, hardware)';
COMMENT ON TABLE t_banco IS 'Informações bancárias dos utilizadores (IBAN, SWIFT, titular)';
COMMENT ON COLUMN t_wallet.wallet_type IS 'Tipo: hot (online), cold (offline), hardware (Ledger/Trezor), exchange, defi';
COMMENT ON COLUMN t_wallet.is_primary IS 'Wallet principal do utilizador (apenas 1 por user)';
COMMENT ON COLUMN t_wallet.stake_address IS 'Endereço de staking (stake1...) para Cardano';
COMMENT ON COLUMN t_banco.iban IS 'IBAN no formato internacional (ex: PT50...)';
COMMENT ON COLUMN t_banco.swift_bic IS 'Código SWIFT/BIC para transferências internacionais';
COMMENT ON COLUMN t_banco.account_type IS 'Tipo de conta: checking (à ordem), savings (poupança), business (empresarial), investment';

-- Cardano
COMMENT ON TABLE t_cardano_transactions IS 'Raw Cardano transactions per tracked wallet. Same tx_hash can appear multiple times for different wallets (e.g., inter-wallet transfers).';
COMMENT ON TABLE t_cardano_tx_io IS 'Per-IO breakdown for tracked wallet address; ADA in lovelace, tokens by policy/asset_name.';
COMMENT ON TABLE t_cardano_assets IS 'Resolved metadata for Cardano native tokens (name/decimals).';
COMMENT ON TABLE t_cardano_sync_state IS 'Incremental sync state for Cardano wallets.';

-- Transações e Shares
COMMENT ON TABLE t_transactions IS 'Transações V2 com suporte multi-asset e multi-conta';
COMMENT ON TABLE t_user_shares IS 'Sistema de ownership baseado em NAV (como fundos de investimento)';

-- ========================================
-- FIM DO SCHEMA
-- ========================================
