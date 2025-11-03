"""
Módulo para gestão de wallets dos utilizadores.
Permite CRUD de wallets (Cardano, Ethereum, Bitcoin, etc.)
"""
import psycopg2
from typing import List, Dict, Optional, Tuple
from database.connection import get_connection

def get_all_wallets(user_id: Optional[int] = None) -> List[Dict]:
    """
    Retorna todas as wallets.
    Se user_id fornecido, retorna apenas wallets desse utilizador.
    """
    conn = get_connection()
    cur = conn.cursor()
    
    if user_id:
        query = """
            SELECT w.wallet_id, w.user_id, u.username, w.wallet_name, w.wallet_type,
                   w.blockchain, w.address, w.stake_address, w.is_active, w.is_primary,
                   w.balance_last_sync, w.notes, w.created_at, w.updated_at
            FROM t_wallet w
            JOIN t_users u ON w.user_id = u.user_id
            WHERE w.user_id = %s
            ORDER BY w.is_primary DESC, w.wallet_name
        """
        cur.execute(query, (user_id,))
    else:
        query = """
            SELECT w.wallet_id, w.user_id, u.username, w.wallet_name, w.wallet_type,
                   w.blockchain, w.address, w.stake_address, w.is_active, w.is_primary,
                   w.balance_last_sync, w.notes, w.created_at, w.updated_at
            FROM t_wallet w
            JOIN t_users u ON w.user_id = u.user_id
            ORDER BY u.username, w.is_primary DESC, w.wallet_name
        """
        cur.execute(query)
    
    columns = [desc[0] for desc in cur.description]
    wallets = [dict(zip(columns, row)) for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return wallets

def get_active_wallets(user_id: Optional[int] = None) -> List[Dict]:
    """Retorna apenas wallets ativas."""
    conn = get_connection()
    cur = conn.cursor()
    
    if user_id:
        query = """
            SELECT wallet_id, wallet_name, wallet_type, blockchain, address, 
                   stake_address, is_primary
            FROM t_wallet
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY is_primary DESC, wallet_name
        """
        cur.execute(query, (user_id,))
    else:
        query = """
            SELECT w.wallet_id, w.user_id, u.username, w.wallet_name, w.wallet_type,
                   w.blockchain, w.address, w.stake_address, w.is_primary
            FROM t_wallet w
            JOIN t_users u ON w.user_id = u.user_id
            WHERE w.is_active = TRUE
            ORDER BY u.username, w.is_primary DESC, w.wallet_name
        """
        cur.execute(query)
    
    columns = [desc[0] for desc in cur.description]
    wallets = [dict(zip(columns, row)) for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return wallets

def get_wallet_by_id(wallet_id: int) -> Optional[Dict]:
    """Retorna wallet específica pelo ID."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT w.wallet_id, w.user_id, u.username, w.wallet_name, w.wallet_type,
               w.blockchain, w.address, w.stake_address, w.is_active, w.is_primary,
               w.balance_last_sync, w.notes
        FROM t_wallet w
        JOIN t_users u ON w.user_id = u.user_id
        WHERE w.wallet_id = %s
    """, (wallet_id,))
    
    row = cur.fetchone()
    
    if row:
        columns = [desc[0] for desc in cur.description]
        wallet = dict(zip(columns, row))
    else:
        wallet = None
    
    cur.close()
    conn.close()
    
    return wallet

def create_wallet(
    user_id: int,
    wallet_name: str,
    wallet_type: str,
    blockchain: str,
    address: str,
    stake_address: Optional[str] = None,
    is_active: bool = True,
    is_primary: bool = False,
    notes: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Cria nova wallet.
    
    Args:
        wallet_type: 'hot', 'cold', 'hardware', 'exchange', 'defi'
        
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
    """
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Se is_primary=True, desmarcar outras wallets desse user
        if is_primary:
            cur.execute("""
                UPDATE t_wallet
                SET is_primary = FALSE
                WHERE user_id = %s
            """, (user_id,))
        
        cur.execute("""
            INSERT INTO t_wallet 
            (user_id, wallet_name, wallet_type, blockchain, address, stake_address,
             is_active, is_primary, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING wallet_id
        """, (user_id, wallet_name, wallet_type, blockchain, address, stake_address,
              is_active, is_primary, notes))
        
        wallet_id = cur.fetchone()[0]
        conn.commit()
        
        cur.close()
        conn.close()
        
        return True, f"Wallet '{wallet_name}' criada com sucesso (ID: {wallet_id})"
    
    except psycopg2.IntegrityError as e:
        conn.rollback()
        cur.close()
        conn.close()
        if "t_wallet_user_id_address_key" in str(e):
            return False, f"Endereço já cadastrado para este utilizador"
        return False, f"Erro de integridade: {str(e)}"
    
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return False, f"Erro ao criar wallet: {str(e)}"

def update_wallet(
    wallet_id: int,
    wallet_name: Optional[str] = None,
    wallet_type: Optional[str] = None,
    blockchain: Optional[str] = None,
    address: Optional[str] = None,
    stake_address: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_primary: Optional[bool] = None,
    notes: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Atualiza wallet.
    Apenas os campos fornecidos são atualizados.
    
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
    """
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Se is_primary=True, desmarcar outras wallets desse user
        if is_primary:
            cur.execute("""
                UPDATE t_wallet
                SET is_primary = FALSE
                WHERE user_id = (SELECT user_id FROM t_wallet WHERE wallet_id = %s)
                AND wallet_id != %s
            """, (wallet_id, wallet_id))
        
        # Construir query dinâmica
        updates = []
        params = []
        
        if wallet_name is not None:
            updates.append("wallet_name = %s")
            params.append(wallet_name)
        if wallet_type is not None:
            updates.append("wallet_type = %s")
            params.append(wallet_type)
        if blockchain is not None:
            updates.append("blockchain = %s")
            params.append(blockchain)
        if address is not None:
            updates.append("address = %s")
            params.append(address)
        if stake_address is not None:
            updates.append("stake_address = %s")
            params.append(stake_address)
        if is_active is not None:
            updates.append("is_active = %s")
            params.append(is_active)
        if is_primary is not None:
            updates.append("is_primary = %s")
            params.append(is_primary)
        if notes is not None:
            updates.append("notes = %s")
            params.append(notes)
        
        if not updates:
            conn.close()
            cur.close()
            return False, "Nenhum campo para atualizar"
        
        params.append(wallet_id)
        query = f"""
            UPDATE t_wallet
            SET {', '.join(updates)}
            WHERE wallet_id = %s
        """
        
        cur.execute(query, params)
        
        if cur.rowcount == 0:
            conn.rollback()
            cur.close()
            conn.close()
            return False, f"Wallet com ID {wallet_id} não encontrada"
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True, f"Wallet atualizada com sucesso"
    
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return False, f"Erro ao atualizar wallet: {str(e)}"

def delete_wallet(wallet_id: int) -> Tuple[bool, str]:
    """Remove wallet."""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM t_wallet WHERE wallet_id = %s", (wallet_id,))
        
        if cur.rowcount == 0:
            conn.rollback()
            cur.close()
            conn.close()
            return False, f"Wallet com ID {wallet_id} não encontrada"
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True, f"Wallet removida com sucesso"
    
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return False, f"Erro ao remover wallet: {str(e)}"

def set_primary_wallet(wallet_id: int) -> Tuple[bool, str]:
    """Define wallet como principal (desmarca outras do mesmo user)."""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Desmarcar outras wallets do mesmo user
        cur.execute("""
            UPDATE t_wallet
            SET is_primary = FALSE
            WHERE user_id = (SELECT user_id FROM t_wallet WHERE wallet_id = %s)
        """, (wallet_id,))
        
        # Marcar esta como principal
        cur.execute("""
            UPDATE t_wallet
            SET is_primary = TRUE
            WHERE wallet_id = %s
        """, (wallet_id,))
        
        if cur.rowcount == 0:
            conn.rollback()
            cur.close()
            conn.close()
            return False, f"Wallet com ID {wallet_id} não encontrada"
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True, f"Wallet definida como principal"
    
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return False, f"Erro ao definir wallet principal: {str(e)}"

def update_balance_sync(wallet_id: int) -> Tuple[bool, str]:
    """Atualiza timestamp da última sincronização de saldo."""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE t_wallet
            SET balance_last_sync = CURRENT_TIMESTAMP
            WHERE wallet_id = %s
        """, (wallet_id,))
        
        if cur.rowcount == 0:
            conn.rollback()
            cur.close()
            conn.close()
            return False, f"Wallet com ID {wallet_id} não encontrada"
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True, f"Timestamp de sincronização atualizado"
    
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return False, f"Erro ao atualizar sincronização: {str(e)}"
