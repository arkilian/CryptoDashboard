-- Users
CREATE TABLE t_users (
    user_id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE
);

-- Fee Settings (com histórico)
CREATE TABLE t_fee_settings (
    setting_id SERIAL PRIMARY KEY,
    maintenance_rate NUMERIC(6,4) NOT NULL DEFAULT 0.0025,
    maintenance_min NUMERIC(10,2) NOT NULL DEFAULT 3.00,
    performance_rate NUMERIC(6,4) NOT NULL DEFAULT 0.10,
    valid_from TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Snapshots do fundo
CREATE TABLE t_portfolio_snapshots (
    snapshot_id SERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    total_value NUMERIC(18,2) NOT NULL
);

-- Holdings de cada snapshot
CREATE TABLE t_portfolio_holdings (
    holding_id SERIAL PRIMARY KEY,
    snapshot_id INT REFERENCES t_portfolio_snapshots(snapshot_id) ON DELETE CASCADE,
    asset_symbol TEXT NOT NULL,
    quantity NUMERIC(18,6) NOT NULL,
    price NUMERIC(18,6) NOT NULL,
    valor_total NUMERIC(18,2) NOT NULL
);

-- Snapshots de cada utilizador
CREATE TABLE t_user_snapshots (
    user_snapshot_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES t_users(user_id),
    snapshot_date DATE NOT NULL,
    valor_antes NUMERIC(18,2),
    valor_depois NUMERIC(18,2)
);

-- High Water Mark
CREATE TABLE t_user_high_water (
    user_id INT PRIMARY KEY REFERENCES t_users(user_id),
    high_water_value NUMERIC(18,2) NOT NULL
);

-- Histórico de taxas aplicadas
CREATE TABLE t_user_fees (
    fee_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES t_users(user_id),
    fee_type TEXT CHECK (fee_type IN ('maintenance','performance')),
    amount NUMERIC(18,2) NOT NULL,
    fee_date DATE NOT NULL
);

-- Inserir taxas iniciais
INSERT INTO t_fee_settings (maintenance_rate, maintenance_min, performance_rate)
VALUES (0.0025, 3.00, 0.10);
