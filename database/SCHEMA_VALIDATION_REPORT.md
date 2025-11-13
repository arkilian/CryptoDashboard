# 📋 Relatório de Validação do Schema

**Data:** 13/11/2025  
**Base de Dados:** patch  
**Versão Schema:** 2.0 (completo com migrações)

---

## ✅ Validação Completa

### 🎯 Objetivo
Confirmar que o `schema.sql` contém **todas** as alterações de:
- `new_tables.sql`
- `migrations/20251103_cardano_tx_v3.sql`
- `migrations/20251104_api_coingecko.sql`
- `migrations/20251107_cardano_tx_composite_pk.sql`
- `migrations/add_created_at_to_users.sql`

---

## ✅ Itens Verificados e Adicionados

### 1. ✅ Primary Keys Compostas

#### `t_cardano_assets`
```sql
CONSTRAINT pk_cardano_assets PRIMARY KEY (policy_id, asset_name_hex)
```
- **Motivo:** Permite identificar assets nativos Cardano sem usar SERIAL
- **Fonte:** `migrations/20251103_cardano_tx_v3.sql`

#### `t_cardano_transactions`
```sql
CONSTRAINT t_cardano_transactions_pkey PRIMARY KEY (tx_hash, wallet_id)
```
- **Motivo:** Permite mesma transação aparecer em múltiplos wallets (transferências inter-wallet)
- **Fonte:** `migrations/20251107_cardano_tx_composite_pk.sql`

---

### 2. ✅ Foreign Key Composta em `t_cardano_tx_io`

```sql
CONSTRAINT t_cardano_tx_io_tx_fkey 
    FOREIGN KEY (tx_hash, wallet_id) 
    REFERENCES t_cardano_transactions(tx_hash, wallet_id) 
    ON DELETE CASCADE
```
- **Motivo:** Manter integridade referencial com PK composta
- **Fonte:** `migrations/20251107_cardano_tx_composite_pk.sql`

---

### 3. ✅ Tabela `t_cardano_sync_state`

```sql
CREATE TABLE IF NOT EXISTS t_cardano_sync_state (
    wallet_id INTEGER PRIMARY KEY REFERENCES t_wallet(wallet_id) ON DELETE CASCADE,
    last_block_height INTEGER,
    last_tx_timestamp TIMESTAMP WITH TIME ZONE,
    last_synced_at TIMESTAMP WITH TIME ZONE
);
```
- **Motivo:** Tracking de sync incremental por wallet
- **Fonte:** `migrations/20251103_cardano_tx_v3.sql`

---

### 4. ✅ Estrutura Completa de Tabelas API

#### `t_api_coingecko`
```sql
CREATE TABLE IF NOT EXISTS t_api_coingecko (
    api_id SERIAL PRIMARY KEY,
    api_name TEXT,
    api_key TEXT,
    base_url TEXT,
    rate_limit INTEGER,
    timeout INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```
- **Fonte:** `migrations/20251104_api_coingecko.sql` + `new_tables.sql`

#### `t_api_cardano`
```sql
CREATE TABLE IF NOT EXISTS t_api_cardano (
    api_id SERIAL PRIMARY KEY,
    api_name TEXT,
    wallet_id INTEGER REFERENCES t_wallet(wallet_id),
    api_key TEXT,
    base_url TEXT,
    default_address TEXT,
    rate_limit INTEGER,
    timeout INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```
- **Fonte:** `new_tables.sql`

---

### 5. ✅ Estrutura Completa de Wallets e Bancos

#### `t_wallet`
```sql
CREATE TABLE IF NOT EXISTS t_wallet (
    wallet_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES t_users(user_id),
    wallet_name TEXT NOT NULL,
    wallet_type TEXT,  -- hot, cold, hardware, exchange, defi
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
```
- **Fonte:** `new_tables.sql`

#### `t_banco`
```sql
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
    account_type TEXT,  -- checking, savings, business, investment
    is_active BOOLEAN DEFAULT TRUE,
    is_primary BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```
- **Fonte:** `new_tables.sql`

---

### 6. ✅ Triggers para `updated_at`

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_wallet_updated_at
    BEFORE UPDATE ON t_wallet
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_banco_updated_at
    BEFORE UPDATE ON t_banco
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_cardano_updated_at
    BEFORE UPDATE ON t_api_cardano
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_coingecko_updated_at
    BEFORE UPDATE ON t_api_coingecko
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```
- **Fonte:** `new_tables.sql`

---

### 7. ✅ Views Úteis

#### `v_user_active_wallets`
```sql
CREATE OR REPLACE VIEW v_user_active_wallets AS
SELECT 
    w.wallet_id, w.user_id, u.username,
    w.wallet_name, w.wallet_type, w.blockchain,
    w.address, w.stake_address, w.is_primary, w.balance_last_sync
FROM t_wallet w
JOIN t_users u ON w.user_id = u.user_id
WHERE w.is_active = TRUE
ORDER BY u.username, w.is_primary DESC, w.wallet_name;
```

#### `v_user_active_banks`
```sql
CREATE OR REPLACE VIEW v_user_active_banks AS
SELECT 
    b.banco_id, b.user_id, u.username,
    b.bank_name, b.account_holder, b.iban, b.swift_bic,
    b.currency, b.is_primary
FROM t_banco b
JOIN t_users u ON b.user_id = u.user_id
WHERE b.is_active = TRUE
ORDER BY u.username, b.is_primary DESC, b.bank_name;
```

#### `v_active_apis`
```sql
CREATE OR REPLACE VIEW v_active_apis AS
SELECT 
    api_id, api_name, base_url, rate_limit, timeout,
    created_at, updated_at
FROM t_api_cardano
WHERE is_active = TRUE
ORDER BY api_name;
```

#### `v_cardano_daily_deltas`
```sql
CREATE OR REPLACE VIEW v_cardano_daily_deltas AS
WITH io AS (
    SELECT 
        t.tx_timestamp::date AS dt,
        i.wallet_id, i.policy_id, i.asset_name_hex,
        SUM(CASE WHEN i.io_type = 'output' THEN COALESCE(i.lovelace, 0) 
                 ELSE -COALESCE(i.lovelace, 0) END) AS net_lovelace,
        SUM(CASE WHEN i.io_type = 'output' THEN COALESCE(i.token_value_raw, 0) 
                 ELSE -COALESCE(i.token_value_raw, 0) END) AS net_token_raw
    FROM t_cardano_tx_io i
    JOIN t_cardano_transactions t ON t.tx_hash = i.tx_hash AND t.wallet_id = i.wallet_id
    GROUP BY 1,2,3,4
)
SELECT * FROM io;
```
- **Fonte:** `new_tables.sql` + `migrations/20251103_cardano_tx_v3.sql`

---

### 8. ✅ Comentários de Documentação

```sql
-- APIs
COMMENT ON TABLE t_api_cardano IS 'Configurações de APIs para consultas blockchain (inicialmente Cardano)';
COMMENT ON TABLE t_api_coingecko IS 'Configurações de API do CoinGecko para preços de criptomoedas';

-- Wallets e Bancos
COMMENT ON TABLE t_wallet IS 'Gestão de wallets dos utilizadores (hot, cold, hardware)';
COMMENT ON TABLE t_banco IS 'Informações bancárias dos utilizadores (IBAN, SWIFT, titular)';

-- Cardano
COMMENT ON TABLE t_cardano_transactions IS 'Raw Cardano transactions per tracked wallet. Same tx_hash can appear multiple times for different wallets (e.g., inter-wallet transfers).';
COMMENT ON TABLE t_cardano_tx_io IS 'Per-IO breakdown for tracked wallet address; ADA in lovelace, tokens by policy/asset_name.';
COMMENT ON TABLE t_cardano_assets IS 'Resolved metadata for Cardano native tokens (name/decimals).';
COMMENT ON TABLE t_cardano_sync_state IS 'Incremental sync state for Cardano wallets.';
```
- **Fonte:** `new_tables.sql` + `migrations/20251103_cardano_tx_v3.sql`

---

### 9. ✅ Coluna `created_at` em `t_users`

```sql
CREATE TABLE IF NOT EXISTS t_users (
    user_id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP  -- ✅ ADICIONADO
);
```
- **Fonte:** `migrations/add_created_at_to_users.sql`

---

## 📊 Teste de Compatibilidade

```
======================================================================
TESTE DE COMPATIBILIDADE: SCHEMA vs DATA EXPORT
======================================================================

📋 Tabelas no schema: 29
📊 Tabelas com dados: 20

✓ t_gender: OK (2 colunas)
✓ t_users: OK (6 colunas)
✓ t_exchanges: OK (3 colunas)
✓ t_assets: OK (6 colunas)
✓ t_fee_settings: OK (5 colunas)
✓ t_tags: OK (4 colunas)
✓ t_address: OK (6 colunas)
✓ t_user_profile: OK (10 colunas)
✓ t_exchange_accounts: OK (5 colunas)
✓ t_wallet: OK (13 colunas)                    ✅
✓ t_banco: OK (16 colunas)                     ✅
✓ t_api_coingecko: OK (10 colunas)             ✅
✓ t_api_cardano: OK (11 colunas)               ✅
✓ t_cardano_assets: OK (4 colunas)             ✅
✓ t_user_capital_movements: OK (7 colunas)
✓ t_transactions: OK (21 colunas)
✓ t_price_snapshots: OK (6 colunas)
✓ t_user_shares: OK (11 colunas)
✓ t_cardano_transactions: OK (9 colunas)       ✅
✓ t_cardano_tx_io: OK (11 colunas)             ✅

======================================================================
✅ COMPATIBILIDADE: OK
   Todas as colunas dos INSERTs existem no schema!
======================================================================
```

---

## 📋 Tabelas no Schema (29 total)

1. ✅ t_users
2. ✅ t_gender
3. ✅ t_address
4. ✅ t_user_profile
5. ✅ t_fee_settings
6. ✅ t_user_high_water
7. ✅ t_user_fees
8. ✅ t_exchanges
9. ✅ t_assets
10. ✅ t_exchange_accounts
11. ✅ t_user_capital_movements
12. ✅ t_transactions
13. ✅ t_price_snapshots
14. ✅ t_portfolio_snapshots
15. ✅ t_portfolio_holdings
16. ✅ t_user_snapshots
17. ✅ t_user_manual_snapshots
18. ✅ t_snapshot_assets
19. ✅ t_tags
20. ✅ t_transaction_tags
21. ✅ t_user_shares
22. ✅ t_wallet
23. ✅ t_banco
24. ✅ t_api_coingecko
25. ✅ t_api_cardano
26. ✅ t_cardano_assets
27. ✅ t_cardano_transactions
28. ✅ t_cardano_tx_io
29. ✅ t_cardano_sync_state

---

## 🎯 Conclusão

### ✅ SCHEMA COMPLETO E VALIDADO

O ficheiro `schema.sql` contém agora **TODAS** as features de:
- ✅ `new_tables.sql`
- ✅ `migrations/20251103_cardano_tx_v3.sql`
- ✅ `migrations/20251104_api_coingecko.sql`
- ✅ `migrations/20251107_cardano_tx_composite_pk.sql`
- ✅ `migrations/add_created_at_to_users.sql`

### 📦 Ficheiros Prontos para Uso

1. ✅ **schema.sql** - Estrutura completa (versão final)
2. ✅ **data_export.sql** - Dados compatíveis
3. ✅ **test_schema_compatibility.py** - Validação passou 100%

### 🚀 Pronto para Produção

O sistema de backup/restore está **completo e testado**:
- Schema atualizado com todas as migrações
- Dados exportados e validados
- Testes de compatibilidade passaram
- Scripts de setup prontos para Windows e Linux

---

**Última atualização:** 13/11/2025 13:30  
**Status:** ✅ COMPLETO
