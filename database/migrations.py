"""Lightweight runtime migrations.

Helpers to manage schema tweaks at runtime (drop legacy columns, add new ones).
"""
from typing import Optional
from sqlalchemy import text
from .connection import get_engine


def has_is_staking_column() -> bool:
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
                SELECT COUNT(*) > 0 AS exists
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 't_transactions'
                  AND column_name = 'is_staking'
                """
            )
        )
        return bool(result.scalar())


def drop_transactions_staking_column() -> bool:
    """Drops legacy is_staking column if it exists. Safe no-op otherwise."""
    try:
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE t_transactions DROP COLUMN IF EXISTS is_staking"))
        return True
    except Exception:
        return False


# Exchange accounts: account_category column
def has_account_category_column() -> bool:
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
                SELECT COUNT(*) > 0 AS exists
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 't_exchange_accounts'
                  AND column_name = 'account_category'
                """
            )
        )
        return bool(result.scalar())


def ensure_exchange_accounts_category_column() -> bool:
    try:
        if has_account_category_column():
            return True
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE t_exchange_accounts ADD COLUMN IF NOT EXISTS account_category TEXT"))
        return has_account_category_column()
    except Exception:
        return False


# Transactions: account_id column
def has_transactions_account_column() -> bool:
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
                SELECT COUNT(*) > 0 AS exists
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 't_transactions'
                  AND column_name = 'account_id'
                """
            )
        )
        return bool(result.scalar())


def ensure_transactions_account_column() -> bool:
    try:
        if has_transactions_account_column():
            return True
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE t_transactions ADD COLUMN IF NOT EXISTS account_id INT REFERENCES t_exchange_accounts(account_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_transactions_account ON t_transactions(account_id)"))
        return has_transactions_account_column()
    except Exception:
        return False


# ========================================
# MIGRATION V2: Multi-Asset Transaction Model
# ========================================

def apply_transaction_model_v2():
    """
    Aplica o novo modelo de transações que suporta:
    - Operações multi-asset (swap, transfer)
    - Novos tipos: deposit, withdrawal, stake, unstake, reward, lend, borrow, etc.
    - Colunas: from_asset_id, to_asset_id, from_quantity, to_quantity, from_account_id, to_account_id, fee_asset_id
    
    Esta migração é IDEMPOTENTE (pode ser executada múltiplas vezes sem problemas).
    """
    try:
        engine = get_engine()
        with engine.begin() as conn:
            # 1. Drop old CHECK constraint if exists
            conn.execute(text("""
                ALTER TABLE t_transactions 
                DROP CONSTRAINT IF EXISTS t_transactions_transaction_type_check
            """))
            
            # 2. Add new columns (IF NOT EXISTS para segurança)
            conn.execute(text("""
                ALTER TABLE t_transactions 
                ADD COLUMN IF NOT EXISTS from_asset_id INT REFERENCES t_assets(asset_id)
            """))
            conn.execute(text("""
                ALTER TABLE t_transactions 
                ADD COLUMN IF NOT EXISTS to_asset_id INT REFERENCES t_assets(asset_id)
            """))
            conn.execute(text("""
                ALTER TABLE t_transactions 
                ADD COLUMN IF NOT EXISTS from_quantity NUMERIC(36,8)
            """))
            conn.execute(text("""
                ALTER TABLE t_transactions 
                ADD COLUMN IF NOT EXISTS to_quantity NUMERIC(36,8)
            """))
            conn.execute(text("""
                ALTER TABLE t_transactions 
                ADD COLUMN IF NOT EXISTS from_account_id INT REFERENCES t_exchange_accounts(account_id)
            """))
            conn.execute(text("""
                ALTER TABLE t_transactions 
                ADD COLUMN IF NOT EXISTS to_account_id INT REFERENCES t_exchange_accounts(account_id)
            """))
            conn.execute(text("""
                ALTER TABLE t_transactions 
                ADD COLUMN IF NOT EXISTS fee_asset_id INT REFERENCES t_assets(asset_id)
            """))
            conn.execute(text("""
                ALTER TABLE t_transactions 
                ADD COLUMN IF NOT EXISTS fee_quantity NUMERIC(36,8) DEFAULT 0
            """))
            
            # 3. Add new CHECK constraint with all transaction types
            conn.execute(text("""
                ALTER TABLE t_transactions 
                ADD CONSTRAINT t_transactions_transaction_type_check 
                CHECK (transaction_type IN (
                    'buy', 'sell',              
                    'deposit', 'withdrawal',    
                    'swap',                     
                    'transfer',                 
                    'stake', 'unstake',         
                    'reward',                   
                    'lend', 'borrow', 'repay',  
                    'liquidate'
                ))
            """))

            # 3.1. Relax legacy NOT NULL constraints to support V2 records without legacy fields
            # These operations are idempotent; DROP NOT NULL when still present
            try:
                conn.execute(text("ALTER TABLE t_transactions ALTER COLUMN asset_id DROP NOT NULL"))
            except Exception:
                pass
            try:
                conn.execute(text("ALTER TABLE t_transactions ALTER COLUMN quantity DROP NOT NULL"))
            except Exception:
                pass
            try:
                conn.execute(text("ALTER TABLE t_transactions ALTER COLUMN price_eur DROP NOT NULL"))
            except Exception:
                pass
            try:
                conn.execute(text("ALTER TABLE t_transactions ALTER COLUMN total_eur DROP NOT NULL"))
            except Exception:
                pass
            
            # 4. Create indexes for new columns
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_transactions_from_asset 
                ON t_transactions(from_asset_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_transactions_to_asset 
                ON t_transactions(to_asset_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_transactions_from_account 
                ON t_transactions(from_account_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_transactions_to_account 
                ON t_transactions(to_account_id)
            """))
            
            # 5. Ensure EUR asset exists
            conn.execute(text("""
                INSERT INTO t_assets (symbol, name, chain, coingecko_id, is_stablecoin) 
                VALUES ('EUR', 'Euro', NULL, NULL, TRUE)
                ON CONFLICT (symbol) DO NOTHING
            """))
            
            # 6. Ensure "Banco" exchange exists
            conn.execute(text("""
                INSERT INTO t_exchanges (name, category) 
                VALUES ('Banco', 'FIAT')
                ON CONFLICT DO NOTHING
            """))
            
            # 7. Migrate legacy buy/sell transactions to new format
            # (Apenas para transações que ainda não têm from_/to_ preenchidos)
            conn.execute(text("""
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
                    AND to_asset_id IS NULL
            """))
            
        return True
    except Exception as e:
        print(f"Error applying transaction model v2: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_transaction_model_v2() -> bool:
    """Verifica se a migration v2 já foi aplicada (inclui nullability dos campos legacy)."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Verifica se from_asset_id existe
            has_from = conn.execute(text("""
                SELECT COUNT(*) > 0 AS exists
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 't_transactions'
                  AND column_name = 'from_asset_id'
            """))
            if not bool(has_from.scalar()):
                return False

            # Verifica se colunas legacy são NULLABLE
            def is_nullable(col: str) -> bool:
                r = conn.execute(text(
                    """
                    SELECT is_nullable = 'YES' AS ok
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 't_transactions'
                      AND column_name = :col
                    """
                ), {"col": col})
                val = r.scalar()
                return bool(val) if val is not None else False

            legacy_ok = all([
                is_nullable('asset_id'),
                is_nullable('quantity'),
                is_nullable('price_eur'),
                is_nullable('total_eur'),
            ])
            return legacy_ok
    except Exception:
        return False
