#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verifica wallet_ids das transações."""

from database.connection import get_connection, return_connection

def check_wallet_ids():
    conn = get_connection()
    cur = conn.cursor()
    
    # Wallet 2 info
    cur.execute("SELECT wallet_name FROM t_wallet WHERE wallet_id = 2")
    wallet_name = cur.fetchone()
    print(f"📌 Wallet 2: {wallet_name[0] if wallet_name else 'NOT FOUND'}\n")
    
    # Check specific transaction
    tx_hash = '2cf89fd74718ce9d747c43c1388a0e27d52ed348ed8818d4199bd1321a55964e'
    cur.execute("""
        SELECT wallet_id, tx_timestamp, status
        FROM t_cardano_transactions
        WHERE tx_hash = %s
    """, (tx_hash,))
    row = cur.fetchone()
    
    if row:
        print(f"✅ Transação 2cf89fd7...")
        print(f"   wallet_id: {row[0]}")
        print(f"   timestamp: {row[1]}")
        print(f"   status: {row[2]}\n")
    else:
        print("❌ Transação 2cf89fd7... NÃO ENCONTRADA\n")
    
    # Count by wallet_id
    print("📊 Contagem por wallet_id:")
    cur.execute("""
        SELECT wallet_id, COUNT(*) as cnt, COUNT(DISTINCT tx_hash) as unique_cnt
        FROM t_cardano_transactions
        GROUP BY wallet_id
        ORDER BY wallet_id
    """)
    
    for row in cur.fetchall():
        wallet_id, cnt, unique_cnt = row
        dupe_flag = " ⚠️ DUPLICADOS!" if cnt != unique_cnt else ""
        print(f"   Wallet {wallet_id}: {cnt} rows, {unique_cnt} unique tx_hash{dupe_flag}")
    
    # Check for duplicates in wallet 2
    print("\n🔍 Verificar duplicados no wallet 2:")
    cur.execute("""
        SELECT tx_hash, COUNT(*) as cnt
        FROM t_cardano_transactions
        WHERE wallet_id = 2
        GROUP BY tx_hash
        HAVING COUNT(*) > 1
    """)
    
    dupes = cur.fetchall()
    if dupes:
        print(f"   ⚠️ {len(dupes)} transações duplicadas:")
        for tx_hash, cnt in dupes:
            print(f"      {tx_hash[:16]}... aparece {cnt}x")
    else:
        print("   ✅ Sem duplicados no wallet 2")
    
    # Unique count for wallet 2
    cur.execute("""
        SELECT COUNT(DISTINCT tx_hash)
        FROM t_cardano_transactions
        WHERE wallet_id = 2
    """)
    unique_count = cur.fetchone()[0]
    print(f"\n📈 Wallet 2 - COUNT(DISTINCT tx_hash): {unique_count}")
    
    return_connection(conn)

if __name__ == "__main__":
    check_wallet_ids()
