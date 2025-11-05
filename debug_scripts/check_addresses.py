#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verifica endereços e transações mal associadas."""

from database.connection import get_connection, return_connection

def check_addresses():
    conn = get_connection()
    cur = conn.cursor()
    
    # Get wallet addresses
    cur.execute("""
        SELECT wallet_id, wallet_name, address
        FROM t_wallet
        WHERE wallet_id IN (1, 2)
        ORDER BY wallet_id
    """)
    
    wallets = {}
    for row in cur.fetchall():
        wallet_id, name, address = row
        wallets[wallet_id] = {"name": name, "address": address}
        print(f"📌 Wallet {wallet_id} ({name}):")
        print(f"   Bech32: {address}\n")
    
    # Check misassociated transaction
    tx_hash = '2cf89fd74718ce9d747c43c1388a0e27d52ed348ed8818d4199bd1321a55964e'
    
    # Get inputs for this transaction
    cur.execute("""
        SELECT address, lovelace, policy_id, asset_name_hex, token_value_raw
        FROM t_cardano_tx_io
        WHERE tx_hash = %s AND io_type = 'input'
        ORDER BY io_id
        LIMIT 5
    """, (tx_hash,))
    
    print(f"📥 Inputs da transação 2cf89fd7:")
    for row in cur.fetchall():
        address, lovelace, policy_id, asset_name_hex, token_value = row
        if lovelace:
            print(f"   {address[:20]}... = {lovelace/1000000:.2f} ADA")
        if policy_id:
            print(f"      + {asset_name_hex or 'token'} ({token_value})")
    
    # Get outputs
    cur.execute("""
        SELECT address, lovelace, policy_id, asset_name_hex, token_value_raw
        FROM t_cardano_tx_io
        WHERE tx_hash = %s AND io_type = 'output'
        ORDER BY io_id
    """, (tx_hash,))
    
    print(f"\n📤 Outputs da transação 2cf89fd7:")
    for row in cur.fetchall():
        address, lovelace, policy_id, asset_name_hex, token_value = row
        if lovelace:
            print(f"   {address[:20]}... = {lovelace/1000000:.2f} ADA")
        if policy_id:
            print(f"      + {asset_name_hex or 'token'} ({token_value})")
    
    # Check which wallet owns this tx
    print(f"\n🔍 Verificar ownership:")
    for wallet_id, info in wallets.items():
        wallet_addr = info['address']
        
        # Check if wallet address appears in inputs or outputs
        cur.execute("""
            SELECT COUNT(*)
            FROM t_cardano_tx_io
            WHERE tx_hash = %s AND address = %s
        """, (tx_hash, wallet_addr))
        
        count = cur.fetchone()[0]
        if count > 0:
            print(f"   ✅ Wallet {wallet_id} ({info['name']}) aparece {count}x nesta transação")
        else:
            print(f"   ❌ Wallet {wallet_id} ({info['name']}) NÃO aparece nesta transação")
    
    return_connection(conn)

if __name__ == "__main__":
    check_addresses()
