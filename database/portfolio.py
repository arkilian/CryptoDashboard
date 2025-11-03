from database.connection import get_db_cursor
from services.fees import apply_fees

def insert_snapshot_and_fees(user_id, snapshot_date, df_assets):
    """
    Optimized version: reduces N+1 queries and uses bulk operations.
    """
    with get_db_cursor() as cur:
        total_value = df_assets['valor_total'].sum()

        # Inserir snapshot do portfólio
        cur.execute("""
            INSERT INTO t_portfolio_snapshots (snapshot_date, total_value)
            VALUES (%s, %s) RETURNING snapshot_id
        """, (snapshot_date, total_value))
        snapshot_id = cur.fetchone()[0]

        # Bulk insert assets using executemany for better performance
        # Optimized: Use to_dict() instead of iterrows()
        asset_data = [
            (snapshot_id, row['asset_symbol'], row['quantity'], row['price'], row['valor_total'])
            for row in df_assets.to_dict('records')
        ]
        cur.executemany("""
            INSERT INTO t_portfolio_holdings (snapshot_id, asset_symbol, quantity, price, valor_total)
            VALUES (%s, %s, %s, %s, %s)
        """, asset_data)

        # Obter todos os utilizadores (exceto admin) com seus últimos snapshots em uma única query
        cur.execute("""
            SELECT u.user_id, 
                   COALESCE(
                       (SELECT us.valor_depois 
                        FROM t_user_snapshots us 
                        WHERE us.user_id = u.user_id 
                        ORDER BY us.snapshot_date DESC 
                        LIMIT 1), 
                       0
                   ) as valor_antes
            FROM t_users u
            WHERE u.is_admin = FALSE
        """)
        user_data = cur.fetchall()

        # Process fees for each user
        for uid, valor_antes in user_data:
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
