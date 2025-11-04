#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix cross-wallet transactions before applying composite PK migration.

Problem: Transaction 2cf89fd7... has:
- tx row with wallet_id=1 (ledger)
- IO rows with wallet_id=2 (Vespr)

Solution: Duplicate transaction rows for each wallet that has IO rows.
"""

from database.connection import get_connection, return_connection

def fix_cross_wallet_txs():
    conn = get_connection()
    cur = conn.cursor()
    
    print("🔍 Procurar transações com IO de wallets diferentes...")
    
    # Find transactions where IO wallet_id doesn't match transaction wallet_id
    cur.execute("""
        SELECT DISTINCT 
            i.tx_hash,
            t.wallet_id as tx_wallet,
            i.wallet_id as io_wallet
        FROM t_cardano_tx_io i
        JOIN t_cardano_transactions t ON t.tx_hash = i.tx_hash
        WHERE i.wallet_id != t.wallet_id
        ORDER BY i.tx_hash, i.wallet_id
    """)
    
    mismatches = cur.fetchall()
    if not mismatches:
        print("✅ Sem problemas encontrados!")
        return_connection(conn)
        return
    
    print(f"⚠️ Encontradas {len(mismatches)} rows com mismatch:\n")
    for tx_hash, tx_wallet, io_wallet in mismatches:
        print(f"   TX {tx_hash[:16]}... está em wallet {tx_wallet}, mas tem IO em wallet {io_wallet}")
    
    # Group by tx_hash to see all wallets involved
    print("\n📊 Agrupar por transação:")
    cur.execute("""
        SELECT 
            i.tx_hash,
            t.wallet_id as tx_wallet,
            array_agg(DISTINCT i.wallet_id) as io_wallets
        FROM t_cardano_tx_io i
        JOIN t_cardano_transactions t ON t.tx_hash = i.tx_hash
        GROUP BY i.tx_hash, t.wallet_id
        HAVING COUNT(DISTINCT i.wallet_id) > 1 OR array_agg(DISTINCT i.wallet_id) != ARRAY[t.wallet_id]
    """)
    
    grouped = cur.fetchall()
    for tx_hash, tx_wallet, io_wallets in grouped:
        print(f"\n   TX {tx_hash[:16]}...")
        print(f"      Registada em wallet: {tx_wallet}")
        print(f"      IO encontrados em wallets: {io_wallets}")
        
        # For each missing wallet, duplicate the transaction
        for target_wallet in io_wallets:
            if target_wallet != tx_wallet:
                print(f"      → Duplicar para wallet {target_wallet}")
                
                # Get address for target wallet
                cur.execute("SELECT address FROM t_wallet WHERE wallet_id = %s", (target_wallet,))
                addr_row = cur.fetchone()
                if not addr_row:
                    print(f"         ❌ Wallet {target_wallet} não encontrada!")
                    continue
                target_address = addr_row[0]
                
                # Copy transaction row
                cur.execute("""
                    INSERT INTO t_cardano_transactions 
                        (tx_hash, wallet_id, address, block_height, tx_timestamp, status, fees_ada, raw_payload)
                    SELECT 
                        tx_hash, %s, %s, block_height, tx_timestamp, status, fees_ada, raw_payload
                    FROM t_cardano_transactions
                    WHERE tx_hash = %s AND wallet_id = %s
                    ON CONFLICT (tx_hash) DO NOTHING
                """, (target_wallet, target_address, tx_hash, tx_wallet))
                
                if cur.rowcount > 0:
                    print(f"         ✅ Transação duplicada para wallet {target_wallet}")
                else:
                    print(f"         ⚠️ Transação já existe em wallet {target_wallet}")
    
    conn.commit()
    print("\n✅ Fix concluído! Agora pode aplicar a migration do composite PK.")
    return_connection(conn)

if __name__ == "__main__":
    fix_cross_wallet_txs()
