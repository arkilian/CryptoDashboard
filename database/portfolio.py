from .connection import get_connection
from services.fees import apply_fees

def insert_snapshot_and_fees(user_id, snapshot_date, df_assets):
    conn = get_connection()
    cur = conn.cursor()

    total_value = df_assets['valor_total'].sum()

    # Inserir snapshot do portfólio
    cur.execute("""
        INSERT INTO t_portfolio_snapshots (snapshot_date, total_value)
        VALUES (%s, %s) RETURNING snapshot_id
    """, (snapshot_date, total_value))
    snapshot_id = cur.fetchone()[0]

    # Inserir ativos
    for _, row in df_assets.iterrows():
        cur.execute("""
            INSERT INTO t_portfolio_holdings (snapshot_id, asset_symbol, quantity, price, valor_total)
            VALUES (%s, %s, %s, %s, %s)
        """, (snapshot_id, row['asset_symbol'], row['quantity'], row['price'], row['valor_total']))

    # Obter todos os utilizadores (exceto admin e fees)
    cur.execute("SELECT user_id FROM t_users WHERE user_id NOT IN (1, 2)")
    user_ids = [row[0] for row in cur.fetchall()]

    for uid in user_ids:
        # �ltimo snapshot do utilizador
        cur.execute("""
            SELECT valor_depois FROM t_user_snapshots
            WHERE user_id = %s ORDER BY snapshot_date DESC LIMIT 1
        """, (uid,))
        row = cur.fetchone()
        valor_antes = row[0] if row else 0

        participacao = valor_antes / total_value if total_value > 0 else 0
        valor_user = total_value * participacao

        # Aplicar taxas (maintenance + performance)
        valor_user, fee_manutencao, fee_performance = apply_fees(
            uid, snapshot_date, total_value, valor_user
        )

        # Gravar snapshot do utilizador
        cur.execute("""
            INSERT INTO t_user_snapshots (user_id, snapshot_date, valor_antes, valor_depois)
            VALUES (%s, %s, %s, %s)
        """, (uid, snapshot_date, valor_antes, valor_user))

    conn.commit()
    cur.close()
    conn.close()
