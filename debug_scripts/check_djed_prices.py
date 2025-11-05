"""Verificar snapshots de DJED e DjedMicroUSD."""
from database.connection import get_connection, return_connection

conn = get_connection()
cur = conn.cursor()

print("=" * 70)
print("1. Assets DJED configurados:")
print("=" * 70)
cur.execute("""
    SELECT asset_id, symbol, name, coingecko_id 
    FROM t_assets 
    WHERE coingecko_id = 'djed' OR symbol ILIKE '%djed%'
    ORDER BY symbol
""")
for row in cur.fetchall():
    symbol_short = row[1][:40] + "..." if len(str(row[1])) > 40 else row[1]
    print(f"  asset_id={row[0]:3}, symbol={symbol_short:45}, coingecko_id={row[3]}")

print("\n" + "=" * 70)
print("2. Snapshots de preços guardados (últimos 10):")
print("=" * 70)
cur.execute("""
    SELECT ps.snapshot_date, a.symbol, ps.price_eur, ps.source, ps.created_at
    FROM t_price_snapshots ps
    JOIN t_assets a ON a.asset_id = ps.asset_id
    WHERE a.coingecko_id = 'djed'
    ORDER BY ps.created_at DESC
    LIMIT 10
""")
rows = cur.fetchall()
if not rows:
    print("  ❌ NENHUM snapshot encontrado para assets com coingecko_id='djed'!")
else:
    for row in rows:
        symbol_short = row[1][:30] + "..." if len(str(row[1])) > 30 else row[1]
        print(f"  {row[0]} | {symbol_short:32} | €{row[2]:8.4f} | {row[3]:10} | {row[4]}")

print("\n" + "=" * 70)
print("3. Contagem de transações por wallet:")
print("=" * 70)
cur.execute("""
    SELECT wallet_id, COUNT(*) as tx_count
    FROM t_cardano_transactions
    GROUP BY wallet_id
    ORDER BY wallet_id
""")
for row in cur.fetchall():
    print(f"  wallet_id={row[0]:2} → {row[1]:3} transações")

print("\n" + "=" * 70)
print("4. Transações da wallet 2 (datas):")
print("=" * 70)
cur.execute("""
    SELECT tx_hash, tx_timestamp::date as dt, status
    FROM t_cardano_transactions
    WHERE wallet_id = 2
    ORDER BY tx_timestamp DESC
""")
for row in cur.fetchall():
    print(f"  {row[1]} | {row[0][:16]}... | {row[2]}")

print("\n" + "=" * 70)
print("5. Símbolos únicos nas transações da wallet 2:")
print("=" * 70)
cur.execute("""
    SELECT DISTINCT 
        CASE 
            WHEN io.policy_id IS NULL THEN 'ADA'
            ELSE COALESCE(ca.display_name, io.policy_id)
        END as symbol,
        COUNT(*) as occurrences
    FROM t_cardano_tx_io io
    LEFT JOIN t_cardano_assets ca ON ca.policy_id = io.policy_id AND ca.asset_name_hex = COALESCE(io.asset_name_hex, '')
    WHERE io.wallet_id = 2
    GROUP BY symbol
    ORDER BY symbol
""")
for row in cur.fetchall():
    symbol_short = row[0][:50] + "..." if len(str(row[0])) > 50 else row[0]
    print(f"  {symbol_short:52} → {row[1]:3} IOs")

return_connection(conn)
