-- ========================================
-- NOVAS TABELAS - CONFIGURAÇÕES
-- ========================================
-- Tabelas para gerir configurações de APIs, Wallets e Bancos
-- ========================================

-- ========================================
-- T_API_CARDANO - Configurações de APIs Cardano
-- ========================================
CREATE TABLE IF NOT EXISTS t_api_cardano (
    api_id SERIAL PRIMARY KEY,
    api_name TEXT NOT NULL UNIQUE,  -- Ex: "CardanoScan", "Blockfrost", "Koios"
    api_key TEXT NOT NULL,
    base_url TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    default_address TEXT,  -- Endereço padrão para consultas
    rate_limit INTEGER,  -- Requests por minuto
    timeout INTEGER DEFAULT 10,  -- Timeout em segundos
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_api_cardano_active ON t_api_cardano(is_active);
CREATE INDEX IF NOT EXISTS idx_api_cardano_name ON t_api_cardano(api_name);

-- Dados iniciais (exemplo - valores devem vir do .env)
INSERT INTO t_api_cardano (api_name, api_key, base_url, is_active, rate_limit, timeout) VALUES 
    ('CardanoScan', 'YOUR_API_KEY_HERE', 'https://api.cardanoscan.io/api/v1', TRUE, 60, 10)
ON CONFLICT (api_name) DO NOTHING;

-- ========================================
-- T_WALLET - Gestão de Wallets
-- ========================================
CREATE TABLE IF NOT EXISTS t_wallet (
    wallet_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES t_users(user_id) ON DELETE CASCADE,
    wallet_name TEXT NOT NULL,  -- Ex: "Eternl Principal", "Ledger"
    wallet_type TEXT NOT NULL CHECK (wallet_type IN ('hot', 'cold', 'hardware', 'exchange', 'defi')),
    blockchain TEXT NOT NULL,  -- Ex: "Cardano", "Ethereum", "Bitcoin"
    address TEXT NOT NULL,  -- Endereço público
    stake_address TEXT,  -- Endereço de staking (Cardano específico)
    is_active BOOLEAN DEFAULT TRUE,
    is_primary BOOLEAN DEFAULT FALSE,  -- Wallet principal do utilizador
    balance_last_sync TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, address)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_wallet_user ON t_wallet(user_id);
CREATE INDEX IF NOT EXISTS idx_wallet_blockchain ON t_wallet(blockchain);
CREATE INDEX IF NOT EXISTS idx_wallet_active ON t_wallet(is_active);
CREATE INDEX IF NOT EXISTS idx_wallet_address ON t_wallet(address);
CREATE INDEX IF NOT EXISTS idx_wallet_stake_address ON t_wallet(stake_address);

-- ========================================
-- T_BANCO - Informações Bancárias
-- ========================================
CREATE TABLE IF NOT EXISTS t_banco (
    banco_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES t_users(user_id) ON DELETE CASCADE,
    bank_name TEXT NOT NULL,  -- Ex: "Banco BPI", "Revolut"
    account_holder TEXT NOT NULL,  -- Nome do titular
    iban TEXT,  -- IBAN (formato internacional)
    swift_bic TEXT,  -- Código SWIFT/BIC
    account_number TEXT,  -- Número de conta (formato local)
    currency TEXT DEFAULT 'EUR',  -- Moeda da conta
    country TEXT,  -- País do banco
    branch TEXT,  -- Agência/Balcão
    account_type TEXT CHECK (account_type IN ('checking', 'savings', 'business', 'investment')),  -- Tipo de conta
    is_active BOOLEAN DEFAULT TRUE,
    is_primary BOOLEAN DEFAULT FALSE,  -- Conta principal do utilizador
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_banco_user ON t_banco(user_id);
CREATE INDEX IF NOT EXISTS idx_banco_active ON t_banco(is_active);
CREATE INDEX IF NOT EXISTS idx_banco_iban ON t_banco(iban);
CREATE INDEX IF NOT EXISTS idx_banco_currency ON t_banco(currency);

-- ========================================
-- TRIGGERS PARA ATUALIZAR updated_at
-- ========================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_api_cardano_updated_at
    BEFORE UPDATE ON t_api_cardano
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_wallet_updated_at
    BEFORE UPDATE ON t_wallet
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_banco_updated_at
    BEFORE UPDATE ON t_banco
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- VIEWS ÚTEIS
-- ========================================

-- View de wallets ativas por utilizador
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

-- View de contas bancárias ativas por utilizador
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

-- View de APIs ativas
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
-- COMENTÁRIOS NAS TABELAS
-- ========================================
COMMENT ON TABLE t_api_cardano IS 'Configurações de APIs para consultas blockchain (inicialmente Cardano)';
COMMENT ON TABLE t_wallet IS 'Gestão de wallets dos utilizadores (hot, cold, hardware)';
COMMENT ON TABLE t_banco IS 'Informações bancárias dos utilizadores (IBAN, SWIFT, titular)';

COMMENT ON COLUMN t_api_cardano.api_key IS 'Chave de API (sensível - deve ser encriptada)';
COMMENT ON COLUMN t_api_cardano.default_address IS 'Endereço padrão usado nas consultas';
COMMENT ON COLUMN t_api_cardano.rate_limit IS 'Limite de requests por minuto';

COMMENT ON COLUMN t_wallet.wallet_type IS 'Tipo: hot (online), cold (offline), hardware (Ledger/Trezor), exchange, defi';
COMMENT ON COLUMN t_wallet.is_primary IS 'Wallet principal do utilizador (apenas 1 por user)';
COMMENT ON COLUMN t_wallet.stake_address IS 'Endereço de staking (stake1...) para Cardano';

COMMENT ON COLUMN t_banco.iban IS 'IBAN no formato internacional (ex: PT50...)';
COMMENT ON COLUMN t_banco.swift_bic IS 'Código SWIFT/BIC para transferências internacionais';
COMMENT ON COLUMN t_banco.account_type IS 'Tipo de conta: checking (à ordem), savings (poupança), business (empresarial), investment';
