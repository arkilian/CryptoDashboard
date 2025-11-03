"""
Módulo para gestão de configurações de APIs Cardano.
Permite CRUD de configurações de APIs (CardanoScan, Blockfrost, Koios, etc.)
"""
import psycopg2
from typing import List, Dict, Optional, Tuple
from database.connection import get_connection

def get_all_apis() -> List[Dict]:
    """Retorna todas as APIs cadastradas."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT api_id, api_name, api_key, base_url, is_active, 
               default_address, rate_limit, timeout, notes,
               created_at, updated_at
        FROM t_api_cardano
        ORDER BY api_name
    """)
    
    columns = [desc[0] for desc in cur.description]
    apis = [dict(zip(columns, row)) for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return apis

def get_active_apis() -> List[Dict]:
    """Retorna apenas APIs ativas."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT api_id, api_name, api_key, base_url, 
               default_address, rate_limit, timeout
        FROM t_api_cardano
        WHERE is_active = TRUE
        ORDER BY api_name
    """)
    
    columns = [desc[0] for desc in cur.description]
    apis = [dict(zip(columns, row)) for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return apis

def get_api_by_name(api_name: str) -> Optional[Dict]:
    """Retorna configuração de uma API específica pelo nome."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT api_id, api_name, api_key, base_url, is_active, 
               default_address, rate_limit, timeout, notes
        FROM t_api_cardano
        WHERE api_name = %s
    """, (api_name,))
    
    row = cur.fetchone()
    
    if row:
        columns = [desc[0] for desc in cur.description]
        api = dict(zip(columns, row))
    else:
        api = None
    
    cur.close()
    conn.close()
    
    return api

def create_api(
    api_name: str,
    api_key: str,
    base_url: str,
    is_active: bool = True,
    default_address: Optional[str] = None,
    rate_limit: Optional[int] = None,
    timeout: int = 10,
    notes: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Cria nova configuração de API.
    
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
    """
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO t_api_cardano 
            (api_name, api_key, base_url, is_active, default_address, rate_limit, timeout, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING api_id
        """, (api_name, api_key, base_url, is_active, default_address, rate_limit, timeout, notes))
        
        api_id = cur.fetchone()[0]
        conn.commit()
        
        cur.close()
        conn.close()
        
        return True, f"API '{api_name}' criada com sucesso (ID: {api_id})"
    
    except psycopg2.IntegrityError:
        conn.rollback()
        cur.close()
        conn.close()
        return False, f"API '{api_name}' já existe"
    
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return False, f"Erro ao criar API: {str(e)}"

def update_api(
    api_id: int,
    api_name: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    is_active: Optional[bool] = None,
    default_address: Optional[str] = None,
    rate_limit: Optional[int] = None,
    timeout: Optional[int] = None,
    notes: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Atualiza configuração de API.
    Apenas os campos fornecidos são atualizados.
    
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
    """
    conn = get_connection()
    cur = conn.cursor()
    
    # Construir query dinâmica apenas com campos fornecidos
    updates = []
    params = []
    
    if api_name is not None:
        updates.append("api_name = %s")
        params.append(api_name)
    if api_key is not None:
        updates.append("api_key = %s")
        params.append(api_key)
    if base_url is not None:
        updates.append("base_url = %s")
        params.append(base_url)
    if is_active is not None:
        updates.append("is_active = %s")
        params.append(is_active)
    if default_address is not None:
        updates.append("default_address = %s")
        params.append(default_address)
    if rate_limit is not None:
        updates.append("rate_limit = %s")
        params.append(rate_limit)
    if timeout is not None:
        updates.append("timeout = %s")
        params.append(timeout)
    if notes is not None:
        updates.append("notes = %s")
        params.append(notes)
    
    if not updates:
        return False, "Nenhum campo para atualizar"
    
    params.append(api_id)
    query = f"""
        UPDATE t_api_cardano
        SET {', '.join(updates)}
        WHERE api_id = %s
    """
    
    try:
        cur.execute(query, params)
        
        if cur.rowcount == 0:
            conn.rollback()
            cur.close()
            conn.close()
            return False, f"API com ID {api_id} não encontrada"
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True, f"API atualizada com sucesso"
    
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return False, f"Erro ao atualizar API: {str(e)}"

def delete_api(api_id: int) -> Tuple[bool, str]:
    """
    Remove configuração de API.
    
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
    """
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM t_api_cardano WHERE api_id = %s", (api_id,))
        
        if cur.rowcount == 0:
            conn.rollback()
            cur.close()
            conn.close()
            return False, f"API com ID {api_id} não encontrada"
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True, f"API removida com sucesso"
    
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return False, f"Erro ao remover API: {str(e)}"

def toggle_api_status(api_id: int) -> Tuple[bool, str]:
    """
    Ativa/Desativa uma API.
    
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
    """
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE t_api_cardano
            SET is_active = NOT is_active
            WHERE api_id = %s
            RETURNING is_active
        """, (api_id,))
        
        row = cur.fetchone()
        if not row:
            conn.rollback()
            cur.close()
            conn.close()
            return False, f"API com ID {api_id} não encontrada"
        
        new_status = row[0]
        conn.commit()
        cur.close()
        conn.close()
        
        status_text = "ativada" if new_status else "desativada"
        return True, f"API {status_text} com sucesso"
    
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return False, f"Erro ao alterar status: {str(e)}"
