"""Get wallet 2 address."""
from database.connection import get_connection, return_connection

conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT wallet_id, wallet_name, address FROM t_wallet WHERE wallet_id = 2")
row = cur.fetchone()
if row:
    print(f"Wallet ID: {row[0]}")
    print(f"Nome: {row[1]}")
    print(f"Endereço: {row[2]}")
else:
    print("Wallet 2 não encontrada")
return_connection(conn)
