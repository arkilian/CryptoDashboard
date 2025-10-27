from database.connection import get_connection

def get_current_fee_settings():
    """Obtém a configuração de taxas mais recente."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT maintenance_rate, maintenance_min, performance_rate
        FROM t_fee_settings
        ORDER BY valid_from DESC LIMIT 1
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        return {
            "maintenance_rate": float(row[0]),
            "maintenance_min": float(row[1]),
            "performance_rate": float(row[2]),
        }
    return {"maintenance_rate": 0.0025, "maintenance_min": 3.0, "performance_rate": 0.10}


def apply_fees(user_id, snapshot_date, total_value, valor_user):
    """
    Aplica taxas de manutenção e performance para um utilizador,
    com base na configuração ativa em t_fee_settings.
    """
    fees = get_current_fee_settings()
    maintenance_rate = fees["maintenance_rate"]
    maintenance_min = fees["maintenance_min"]
    performance_rate = fees["performance_rate"]

    conn = get_connection()
    cur = conn.cursor()

    # --- Maintenance Fee ---
    fee_manutencao = max(round(valor_user * maintenance_rate, 2), maintenance_min)

    cur.execute("""
        SELECT 1 FROM t_user_fees
        WHERE user_id = %s AND fee_type = 'maintenance'
          AND date_trunc('month', fee_date) = date_trunc('month', %s::date)
    """, (user_id, snapshot_date))
    manutencao_cobrada = cur.fetchone() is not None

    if not manutencao_cobrada:
        cur.execute("""
            INSERT INTO t_user_fees (user_id, fee_type, amount, fee_date)
            VALUES (%s, 'maintenance', %s, %s)
        """, (user_id, fee_manutencao, snapshot_date))
        valor_user -= fee_manutencao

    # --- Performance Fee ---
    cur.execute("SELECT high_water_value FROM t_user_high_water WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    hwm_anterior = row[0] if row else 0

    performance_fee = 0
    if valor_user > hwm_anterior:
        lucro = valor_user - hwm_anterior
        performance_fee = round(lucro * performance_rate, 2)

        cur.execute("""
            INSERT INTO t_user_fees (user_id, fee_type, amount, fee_date)
            VALUES (%s, 'performance', %s, %s)
        """, (user_id, performance_fee, snapshot_date)) 
        valor_user -= performance_fee

        cur.execute("""
                INSERT INTO t_user_high_water (user_id, high_water_value)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO UPDATE
                    SET high_water_value = EXCLUDED.high_water_value
        """, (user_id, valor_user))

    conn.commit()
    cur.close()
    conn.close()

    return valor_user, fee_manutencao, performance_fee


def update_fee_settings(maintenance_rate, maintenance_min, performance_rate):
    """Cria um novo registo de configuração de taxas (mantém histórico)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO t_fee_settings (maintenance_rate, maintenance_min, performance_rate)
        VALUES (%s, %s, %s)
    """, (maintenance_rate, maintenance_min, performance_rate))
    conn.commit()
    cur.close()
    conn.close()

def get_fee_history():
    """Retorna todas as configurações de taxas ordenadas por data."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT maintenance_rate, maintenance_min, performance_rate, valid_from
        FROM t_fee_settings
        ORDER BY valid_from DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    history = []
    for r in rows:
        history.append({
            "maintenance_rate": float(r[0]),
            "maintenance_min": float(r[1]),
            "performance_rate": float(r[2]),
            "valid_from": r[3]
        })
    return history
