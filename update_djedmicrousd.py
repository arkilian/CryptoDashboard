from database.connection import get_connection, return_connection

conn = get_connection()
cur = conn.cursor()

cur.execute("UPDATE t_assets SET coingecko_id = 'djed', is_stablecoin = true WHERE symbol = 'DJEDMICROUSD'")
conn.commit()
print(f"✅ Atualizado {cur.rowcount} registro(s) de DJEDMICROUSD")

return_connection(conn)
