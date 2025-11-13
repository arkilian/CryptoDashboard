#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Reset transactions for wallet 2 and resync.
- Prints counts before
- Deletes tx + sync state for wallet 2
- Prints counts after
- Optionally triggers sync
"""
import os, sys

# Ensure project root on sys.path when running as a script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.connection import get_connection, return_connection
from services.cardano_sync import sync_all_cardano_wallets_for_user

def counts(cur, wallet_id: int):
    cur.execute("SELECT COUNT(*), COUNT(DISTINCT tx_hash) FROM t_cardano_transactions WHERE wallet_id=%s", (wallet_id,))
    tx_rows, tx_unique = cur.fetchone()
    cur.execute("SELECT COUNT(*), COUNT(DISTINCT tx_hash) FROM t_cardano_tx_io WHERE wallet_id=%s", (wallet_id,))
    io_rows, io_unique = cur.fetchone()
    return tx_rows, tx_unique, io_rows, io_unique

def main():
    wallet_id = 2
    conn = get_connection()
    cur = conn.cursor()

    print(f"📊 Before: wallet {wallet_id}")
    tx_rows, tx_unique, io_rows, io_unique = counts(cur, wallet_id)
    print(f"  t_cardano_transactions: {tx_rows} rows, {tx_unique} unique tx_hash")
    print(f"  t_cardano_tx_io:        {io_rows} rows, {io_unique} unique tx_hash\n")

    # Delete tx for wallet 2 (IO rows cascade)
    print("🗑️ Deleting transactions for wallet 2 (and cascading IO rows)...")
    cur.execute("DELETE FROM t_cardano_transactions WHERE wallet_id=%s", (wallet_id,))

    # Reset sync state
    print("🔁 Resetting sync state for wallet 2...")
    cur.execute("DELETE FROM t_cardano_sync_state WHERE wallet_id=%s", (wallet_id,))

    conn.commit()

    print(f"\n📊 After delete: wallet {wallet_id}")
    tx_rows, tx_unique, io_rows, io_unique = counts(cur, wallet_id)
    print(f"  t_cardano_transactions: {tx_rows} rows, {tx_unique} unique tx_hash")
    print(f"  t_cardano_tx_io:        {io_rows} rows, {io_unique} unique tx_hash\n")

    return_connection(conn)

    # Optional: trigger resync here by uncommenting
    # print("🚀 Triggering resync (max_pages=20)...")
    # res = sync_all_cardano_wallets_for_user(wallet_ids=[wallet_id], max_pages=20)
    # print(f"✅ Sync result: {res}")

if __name__ == "__main__":
    main()
