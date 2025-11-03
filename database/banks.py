"""
Módulo para gestão de informações bancárias dos utilizadores.
Permite CRUD de contas bancárias (IBAN, SWIFT, titular, etc.)
"""
import psycopg2
from typing import List, Dict, Optional, Tuple
from database.connection import get_connection

def get_all_banks(user_id: Optional[int] = None) -> List[Dict]:
    """
    Retorna todas as contas bancárias.
    Se user_id fornecido, retorna apenas contas desse utilizador.
    """
    conn = get_connection()
    cur = conn.cursor()
    
    if user_id:
        query = """
            SELECT b.banco_id, b.user_id, u.username, b.bank_name, b.account_holder,
                   b.iban, b.swift_bic, b.account_number, b.currency, b.country,
                   b.branch, b.account_type, b.is_active, b.is_primary,
                   b.notes, b.created_at, b.updated_at
            FROM t_banco b
            JOIN t_users u ON b.user_id = u.user_id
            WHERE b.user_id = %s
            ORDER BY b.is_primary DESC, b.bank_name
        """
        cur.execute(query, (user_id,))
    else:
        query = """
            SELECT b.banco_id, b.user_id, u.username, b.bank_name, b.account_holder,
                   b.iban, b.swift_bic, b.account_number, b.currency, b.country,
                   b.branch, b.account_type, b.is_active, b.is_primary,
                   b.notes, b.created_at, b.updated_at
            FROM t_banco b
            JOIN t_users u ON b.user_id = u.user_id
            ORDER BY u.username, b.is_primary DESC, b.bank_name
        """
        cur.execute(query)
    
    columns = [desc[0] for desc in cur.description]
    banks = [dict(zip(columns, row)) for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return banks

def get_active_banks(user_id: Optional[int] = None) -> List[Dict]:
    """Retorna apenas contas ativas."""
    conn = get_connection()
    cur = conn.cursor()
    
    if user_id:
        query = """
            SELECT banco_id, bank_name, account_holder, iban, swift_bic, 
                   currency, is_primary
            FROM t_banco
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY is_primary DESC, bank_name
        """
        cur.execute(query, (user_id,))
    else:
        query = """
            SELECT b.banco_id, b.user_id, u.username, b.bank_name, b.account_holder,
                   b.iban, b.swift_bic, b.currency, b.is_primary
            FROM t_banco b
            JOIN t_users u ON b.user_id = u.user_id
            WHERE b.is_active = TRUE
            ORDER BY u.username, b.is_primary DESC, b.bank_name
        """
        cur.execute(query)
    
    columns = [desc[0] for desc in cur.description]
    banks = [dict(zip(columns, row)) for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return banks

def get_bank_by_id(banco_id: int) -> Optional[Dict]:
    """Retorna conta bancária específica pelo ID."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT b.banco_id, b.user_id, u.username, b.bank_name, b.account_holder,
               b.iban, b.swift_bic, b.account_number, b.currency, b.country,
               b.branch, b.account_type, b.is_active, b.is_primary, b.notes
        FROM t_banco b
        JOIN t_users u ON b.user_id = u.user_id
        WHERE b.banco_id = %s
    """, (banco_id,))
    
    row = cur.fetchone()
    
    if row:
        columns = [desc[0] for desc in cur.description]
        bank = dict(zip(columns, row))
    else:
        bank = None
    
    cur.close()
    conn.close()
    
    return bank

def create_bank(
    user_id: int,
    bank_name: str,
    account_holder: str,
    iban: Optional[str] = None,
    swift_bic: Optional[str] = None,
    account_number: Optional[str] = None,
    currency: str = 'EUR',
    country: Optional[str] = None,
    branch: Optional[str] = None,
    account_type: Optional[str] = None,
    is_active: bool = True,
    is_primary: bool = False,
    notes: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Cria nova conta bancária.
    
    Args:
        account_type: 'checking', 'savings', 'business', 'investment'
        
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
    """
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Se is_primary=True, desmarcar outras contas desse user
        if is_primary:
            cur.execute("""
                UPDATE t_banco
                SET is_primary = FALSE
                WHERE user_id = %s
            """, (user_id,))
        
        cur.execute("""
            INSERT INTO t_banco 
            (user_id, bank_name, account_holder, iban, swift_bic, account_number,
             currency, country, branch, account_type, is_active, is_primary, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING banco_id
        """, (user_id, bank_name, account_holder, iban, swift_bic, account_number,
              currency, country, branch, account_type, is_active, is_primary, notes))
        
        banco_id = cur.fetchone()[0]
        conn.commit()
        
        cur.close()
        conn.close()
        
        return True, f"Conta '{bank_name}' criada com sucesso (ID: {banco_id})"
    
    except psycopg2.IntegrityError as e:
        conn.rollback()
        cur.close()
        conn.close()
        return False, f"Erro de integridade: {str(e)}"
    
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return False, f"Erro ao criar conta: {str(e)}"

def update_bank(
    banco_id: int,
    bank_name: Optional[str] = None,
    account_holder: Optional[str] = None,
    iban: Optional[str] = None,
    swift_bic: Optional[str] = None,
    account_number: Optional[str] = None,
    currency: Optional[str] = None,
    country: Optional[str] = None,
    branch: Optional[str] = None,
    account_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_primary: Optional[bool] = None,
    notes: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Atualiza conta bancária.
    Apenas os campos fornecidos são atualizados.
    
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
    """
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Se is_primary=True, desmarcar outras contas desse user
        if is_primary:
            cur.execute("""
                UPDATE t_banco
                SET is_primary = FALSE
                WHERE user_id = (SELECT user_id FROM t_banco WHERE banco_id = %s)
                AND banco_id != %s
            """, (banco_id, banco_id))
        
        # Construir query dinâmica
        updates = []
        params = []
        
        if bank_name is not None:
            updates.append("bank_name = %s")
            params.append(bank_name)
        if account_holder is not None:
            updates.append("account_holder = %s")
            params.append(account_holder)
        if iban is not None:
            updates.append("iban = %s")
            params.append(iban)
        if swift_bic is not None:
            updates.append("swift_bic = %s")
            params.append(swift_bic)
        if account_number is not None:
            updates.append("account_number = %s")
            params.append(account_number)
        if currency is not None:
            updates.append("currency = %s")
            params.append(currency)
        if country is not None:
            updates.append("country = %s")
            params.append(country)
        if branch is not None:
            updates.append("branch = %s")
            params.append(branch)
        if account_type is not None:
            updates.append("account_type = %s")
            params.append(account_type)
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
        
        params.append(banco_id)
        query = f"""
            UPDATE t_banco
            SET {', '.join(updates)}
            WHERE banco_id = %s
        """
        
        cur.execute(query, params)
        
        if cur.rowcount == 0:
            conn.rollback()
            cur.close()
            conn.close()
            return False, f"Conta com ID {banco_id} não encontrada"
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True, f"Conta atualizada com sucesso"
    
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return False, f"Erro ao atualizar conta: {str(e)}"

def delete_bank(banco_id: int) -> Tuple[bool, str]:
    """Remove conta bancária."""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM t_banco WHERE banco_id = %s", (banco_id,))
        
        if cur.rowcount == 0:
            conn.rollback()
            cur.close()
            conn.close()
            return False, f"Conta com ID {banco_id} não encontrada"
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True, f"Conta removida com sucesso"
    
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return False, f"Erro ao remover conta: {str(e)}"

def set_primary_bank(banco_id: int) -> Tuple[bool, str]:
    """Define conta como principal (desmarca outras do mesmo user)."""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Desmarcar outras contas do mesmo user
        cur.execute("""
            UPDATE t_banco
            SET is_primary = FALSE
            WHERE user_id = (SELECT user_id FROM t_banco WHERE banco_id = %s)
        """, (banco_id,))
        
        # Marcar esta como principal
        cur.execute("""
            UPDATE t_banco
            SET is_primary = TRUE
            WHERE banco_id = %s
        """, (banco_id,))
        
        if cur.rowcount == 0:
            conn.rollback()
            cur.close()
            conn.close()
            return False, f"Conta com ID {banco_id} não encontrada"
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True, f"Conta definida como principal"
    
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return False, f"Erro ao definir conta principal: {str(e)}"

def validate_iban(iban: str) -> bool:
    """
    Validação básica de formato IBAN.
    Apenas verifica se tem 15-34 caracteres alfanuméricos.
    """
    if not iban:
        return False
    
    iban_clean = iban.replace(" ", "").replace("-", "").upper()
    
    if len(iban_clean) < 15 or len(iban_clean) > 34:
        return False
    
    if not iban_clean[:2].isalpha() or not iban_clean[2:].isalnum():
        return False
    
    return True
