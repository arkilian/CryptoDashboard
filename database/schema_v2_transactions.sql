-- ========================================
-- TRANSACTION MODEL V2
-- ========================================
-- Novo modelo de transações que suporta:
-- - Operações multi-asset (swap, transfer)
-- - Movimentos entre contas (Binance Spot → Binance Earn)
-- - DeFi operations (stake, unstake, lend, borrow)
-- - Fees em qualquer asset (não apenas EUR)
-- - Rastreamento por localização (account_id)
-- ========================================

-- ========================================
-- 1. NOVOS TIPOS DE TRANSAÇÃO
-- ========================================

-- Expandir CHECK constraint da tabela t_transactions
-- Tipos suportados:
--   'deposit'       - FIAT in (banco → exchange)        | from: EUR (banco), to: EUR (exchange)
--   'withdrawal'    - FIAT out (exchange → banco)       | from: EUR (exchange), to: EUR (banco)
--   'buy'           - FIAT → cripto                     | from: EUR, to: Asset
--   'sell'          - Cripto → FIAT                     | from: Asset, to: EUR
--   'swap'          - Cripto ↔ Cripto                   | from: Asset A, to: Asset B
--   'transfer'      - Mover entre contas/wallets        | from: Asset (conta A), to: Asset (conta B)
--   'stake'         - Lock em staking/earn              | from: Asset (disponível), to: Asset (staked)
--   'unstake'       - Unlock de staking/earn            | from: Asset (staked), to: Asset (disponível)
--   'reward'        - Recompensa recebida               | to: Asset (sem from)
--   'lend'          - Emprestar asset (lending)         | from: Asset (wallet), to: Asset (lending pool)
--   'borrow'        - Pedir emprestado                  | to: Asset (recebido)
--   'repay'         - Devolver empréstimo               | from: Asset
--   'liquidate'     - Liquidação (perda)                | from: Asset

-- ========================================
-- 2. NOVA ESTRUTURA DA TABELA t_transactions
-- ========================================

-- DROP antigo CHECK constraint (se existir)
ALTER TABLE t_transactions DROP CONSTRAINT IF EXISTS t_transactions_transaction_type_check;

-- ADICIONAR novas colunas (com cuidado para não quebrar dados existentes)
ALTER TABLE t_transactions ADD COLUMN IF NOT EXISTS from_asset_id INT REFERENCES t_assets(asset_id);
ALTER TABLE t_transactions ADD COLUMN IF NOT EXISTS to_asset_id INT REFERENCES t_assets(asset_id);
ALTER TABLE t_transactions ADD COLUMN IF NOT EXISTS from_quantity NUMERIC(36,8);
ALTER TABLE t_transactions ADD COLUMN IF NOT EXISTS to_quantity NUMERIC(36,8);
ALTER TABLE t_transactions ADD COLUMN IF NOT EXISTS from_account_id INT REFERENCES t_exchange_accounts(account_id);
ALTER TABLE t_transactions ADD COLUMN IF NOT EXISTS to_account_id INT REFERENCES t_exchange_accounts(account_id);
ALTER TABLE t_transactions ADD COLUMN IF NOT EXISTS fee_asset_id INT REFERENCES t_assets(asset_id);
ALTER TABLE t_transactions ADD COLUMN IF NOT EXISTS fee_quantity NUMERIC(36,8) DEFAULT 0;

-- Adicionar novo CHECK constraint com todos os tipos
ALTER TABLE t_transactions ADD CONSTRAINT t_transactions_transaction_type_check 
CHECK (transaction_type IN (
    'buy', 'sell',              -- Legacy (mantidos para retrocompatibilidade)
    'deposit', 'withdrawal',    -- Movimentos FIAT
    'swap',                     -- Cripto ↔ Cripto
    'transfer',                 -- Entre contas/wallets
    'stake', 'unstake',         -- Staking operations
    'reward',                   -- Recompensas
    'lend', 'borrow', 'repay',  -- Lending/Borrowing
    'liquidate'                 -- Liquidações
));

-- Adicionar índices para as novas colunas
CREATE INDEX IF NOT EXISTS idx_transactions_from_asset ON t_transactions(from_asset_id);
CREATE INDEX IF NOT EXISTS idx_transactions_to_asset ON t_transactions(to_asset_id);
CREATE INDEX IF NOT EXISTS idx_transactions_from_account ON t_transactions(from_account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_to_account ON t_transactions(to_account_id);

-- ========================================
-- 3. ADICIONAR EUR COMO ASSET
-- ========================================

INSERT INTO t_assets (symbol, name, chain, coingecko_id, is_stablecoin) 
VALUES ('EUR', 'Euro', NULL, NULL, TRUE)
ON CONFLICT (symbol) DO NOTHING;

-- ========================================
-- 4. CRIAR EXCHANGE "BANCO" PARA TRACKING DE EUR
-- ========================================

INSERT INTO t_exchanges (name, category) 
VALUES ('Banco', 'FIAT')
ON CONFLICT DO NOTHING;

-- Nota: Cada utilizador pode criar a sua conta "Banco" em t_exchange_accounts
-- Exemplo: INSERT INTO t_exchange_accounts (exchange_id, user_id, name, account_category) 
--          VALUES ((SELECT exchange_id FROM t_exchanges WHERE name='Banco'), 1, 'Conta principal', 'FIAT');

-- ========================================
-- 5. LÓGICA DE CADA TIPO DE TRANSAÇÃO
-- ========================================

-- DEPOSIT (banco → exchange):
--   from_asset_id: EUR
--   from_account_id: conta bancária
--   from_quantity: X EUR
--   to_asset_id: EUR
--   to_account_id: conta exchange (ex: Binance Spot)
--   to_quantity: X EUR
--   fee_eur: taxa de transferência (se aplicável)

-- WITHDRAWAL (exchange → banco):
--   Inverso do deposit

-- BUY (EUR → Cripto):
--   from_asset_id: EUR
--   from_quantity: 100 EUR
--   to_asset_id: ADA (ou outro)
--   to_quantity: 50 ADA
--   account_id: conta onde acontece (Binance Spot)
--   fee_asset_id: EUR (ou ADA, dependendo)
--   fee_quantity: 0.5

-- SELL (Cripto → EUR):
--   Inverso do buy

-- SWAP (ADA → USDC):
--   from_asset_id: ADA
--   from_quantity: 50 ADA
--   to_asset_id: USDC
--   to_quantity: 40 USDC
--   account_id: conta onde acontece (ex: MetaMask, Minswap)
--   fee_asset_id: ADA (taxa de rede na blockchain)
--   fee_quantity: 0.5 ADA

-- TRANSFER (Binance → Wallet):
--   from_asset_id: ADA
--   from_quantity: 100 ADA
--   from_account_id: Binance Spot
--   to_asset_id: ADA (mesmo asset)
--   to_quantity: 99.5 ADA (após fee de rede)
--   to_account_id: MetaMask (ou Ledger)
--   fee_asset_id: ADA
--   fee_quantity: 0.5 ADA

-- STAKE (disponível → staked):
--   from_asset_id: ADA
--   from_quantity: 100 ADA
--   from_account_id: Binance Spot (ou wallet)
--   to_asset_id: ADA
--   to_quantity: 100 ADA
--   to_account_id: Binance Earn (ou pool de staking)
--   fee: geralmente 0

-- UNSTAKE (staked → disponível):
--   Inverso do stake

-- REWARD (recompensa de staking):
--   to_asset_id: ADA
--   to_quantity: 5 ADA
--   to_account_id: conta onde é recebida
--   from_*: NULL (é criação de valor)

-- LEND (fornecer liquidez):
--   from_asset_id: USDC
--   from_quantity: 1000 USDC
--   from_account_id: wallet
--   to_asset_id: USDC (ou token LP)
--   to_quantity: 1000 USDC
--   to_account_id: lending pool
--   fee_asset_id: ETH (gas)

-- BORROW (pedir emprestado):
--   to_asset_id: USDC
--   to_quantity: 500 USDC
--   to_account_id: wallet
--   from_*: NULL (é dívida)

-- REPAY (devolver empréstimo):
--   from_asset_id: USDC
--   from_quantity: 550 USDC (principal + juros)
--   from_account_id: wallet

-- LIQUIDATE (liquidação):
--   from_asset_id: ETH (colateral perdido)
--   from_quantity: 1 ETH
--   from_account_id: lending protocol

-- ========================================
-- 6. VIEW PARA RETROCOMPATIBILIDADE
-- ========================================

-- View que mapeia transações novas para o formato antigo (para queries legacy)
CREATE OR REPLACE VIEW v_transactions_legacy AS
SELECT 
    transaction_id,
    transaction_type,
    CASE 
        WHEN transaction_type IN ('buy', 'sell') THEN asset_id
        WHEN transaction_type IN ('stake', 'unstake', 'reward') THEN to_asset_id
        ELSE COALESCE(to_asset_id, from_asset_id)
    END AS asset_id,
    CASE 
        WHEN transaction_type IN ('buy', 'sell') THEN quantity
        ELSE COALESCE(to_quantity, from_quantity)
    END AS quantity,
    price_eur,
    total_eur,
    fee_eur,
    exchange_id,
    account_id,
    transaction_date,
    executed_by,
    notes,
    created_at
FROM t_transactions;

-- ========================================
-- 7. HELPER PARA MIGRAR TRANSAÇÕES ANTIGAS
-- ========================================

-- Preencher from_/to_ para transações legacy (buy/sell)
-- Executar APENAS UMA VEZ após aplicar schema
UPDATE t_transactions
SET 
    from_asset_id = CASE 
        WHEN transaction_type = 'buy' THEN (SELECT asset_id FROM t_assets WHERE symbol = 'EUR')
        WHEN transaction_type = 'sell' THEN asset_id
    END,
    to_asset_id = CASE 
        WHEN transaction_type = 'buy' THEN asset_id
        WHEN transaction_type = 'sell' THEN (SELECT asset_id FROM t_assets WHERE symbol = 'EUR')
    END,
    from_quantity = CASE 
        WHEN transaction_type = 'buy' THEN total_eur + COALESCE(fee_eur, 0)
        WHEN transaction_type = 'sell' THEN quantity
    END,
    to_quantity = CASE 
        WHEN transaction_type = 'buy' THEN quantity
        WHEN transaction_type = 'sell' THEN total_eur - COALESCE(fee_eur, 0)
    END,
    fee_asset_id = (SELECT asset_id FROM t_assets WHERE symbol = 'EUR'),
    fee_quantity = COALESCE(fee_eur, 0)
WHERE 
    transaction_type IN ('buy', 'sell')
    AND from_asset_id IS NULL
    AND to_asset_id IS NULL;

-- ========================================
-- 8. NOTAS DE IMPLEMENTAÇÃO
-- ========================================

/*
REGRAS:
1. Sempre preencher from_/to_ para novas transações
2. Manter asset_id/quantity/price_eur/total_eur para buy/sell (retrocompat)
3. Para novos tipos, asset_id pode ser NULL
4. fee_eur continua válido para fees em EUR; fee_asset_id+fee_quantity para outros assets
5. account_id sempre deve apontar para a conta "principal" da operação
6. from_account_id/to_account_id apenas para transfers e stakes entre contas

CÁLCULO DE HOLDINGS:
- Holdings = ∑ (to_quantity - from_quantity) por asset + account
- Separar por account_id para rastrear "onde está"
- Exemplo: 
    * Binance Spot: 100 ADA (disponível)
    * Binance Earn: 50 ADA (staked)
    * MetaMask: 30 ADA (wallet)

CÁLCULO DE SALDO EUR:
- Saldo EUR = ∑ movimentos EUR através de deposit/withdrawal
- Subtrair gastos em buy, adicionar recebidos em sell
- Por conta: separar EUR no banco vs EUR na exchange

EXEMPLO COMPLETO DE WORKFLOW:
1. Depositar 1000 EUR (banco → Binance):
   deposit: from_asset=EUR, from_account=Banco, to_account=Binance Spot, 1000 EUR

2. Comprar ADA:
   buy: from_asset=EUR, from_qty=100, to_asset=ADA, to_qty=50, account=Binance Spot

3. Transferir para Binance Earn:
   stake: from_asset=ADA, from_qty=50, from_account=Binance Spot, to_account=Binance Earn

4. Receber recompensa:
   reward: to_asset=ADA, to_qty=2, to_account=Binance Earn

5. Unstake:
   unstake: from_asset=ADA, from_qty=52, from_account=Binance Earn, to_account=Binance Spot

6. Transferir para MetaMask:
   transfer: from_asset=ADA, from_qty=52, from_account=Binance Spot, to_account=MetaMask, fee_asset=ADA, fee_qty=0.5

7. Swap na DEX:
   swap: from_asset=ADA, from_qty=51.5, to_asset=USDC, to_qty=40, account=MetaMask, fee_asset=ADA, fee_qty=0.2

8. Lend USDC:
   lend: from_asset=USDC, from_qty=40, from_account=MetaMask, to_account=Aave, fee_asset=ETH, fee_qty=0.001

RESULTADO FINAL (holdings por conta):
- Banco: 0 EUR
- Binance Spot: 900 EUR, 0 ADA
- Binance Earn: 0 ADA
- MetaMask: 0 ADA, 0 USDC
- Aave: 40 USDC (em lending)
*/
