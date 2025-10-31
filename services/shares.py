"""
Serviço para gestão de shares (propriedade) do fundo.
Sistema NAV-based onde cada utilizador recebe shares proporcionais ao NAV no momento do depósito.
"""

from database.connection import get_db_cursor, get_connection, return_connection
from services.coingecko import get_price_by_symbol
from typing import Optional, Dict, Tuple, List
from datetime import datetime
import streamlit as st


def _execute_query(query: str, params: tuple = None) -> List[Dict]:
    """
    Helper para executar queries e retornar resultados como lista de dicts.
    
    Args:
        query: SQL query
        params: Parâmetros para a query
        
    Returns:
        Lista de dicionários com os resultados
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        
        # Se for INSERT/UPDATE/DELETE sem RETURNING, retornar lista vazia
        if cur.description is None:
            conn.commit()
            return []
        
        # Se tiver resultados, converter para lista de dicts
        columns = [desc[0] for desc in cur.description]
        results = []
        for row in cur.fetchall():
            results.append(dict(zip(columns, row)))
        
        conn.commit()
        cur.close()
        return results
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        return_connection(conn)


def calculate_fund_nav() -> float:
    """
    Calcula o NAV (Net Asset Value) total do fundo.
    NAV = Caixa (EUR) + Valor das Holdings em Cripto
    
    Returns:
        float: NAV total do fundo em EUR
    """
    # 1. Calcular caixa disponível (apenas utilizadores não-admin):
    # caixa = depósitos - levantamentos - gasto em compras + recebido em vendas
    query_cash = """
        WITH capital AS (
            SELECT 
                COALESCE(SUM(COALESCE(uc.credit, 0)), 0) AS total_deposits,
                COALESCE(SUM(COALESCE(uc.debit, 0)), 0)  AS total_withdrawals
            FROM t_user_capital_movements uc
            JOIN t_users u ON u.user_id = uc.user_id
            WHERE u.is_admin = FALSE
        ),
        trades AS (
            SELECT 
                COALESCE(SUM(CASE WHEN transaction_type = 'buy' THEN price_eur * quantity + COALESCE(fee_eur, 0) ELSE 0 END), 0) AS total_spent,
                COALESCE(SUM(CASE WHEN transaction_type = 'sell' THEN (price_eur * quantity) - COALESCE(fee_eur, 0) ELSE 0 END), 0) AS total_received
            FROM t_transactions
        )
        SELECT 
            (c.total_deposits - c.total_withdrawals - t.total_spent + t.total_received) AS cash_balance
        FROM capital c, trades t;
    """
    
    result = _execute_query(query_cash)
    cash_balance = float(result[0]['cash_balance']) if result else 0.0
    
    # 2. Calcular valor das holdings em cripto (a preços atuais)
    query_holdings = """
        SELECT 
            a.symbol,
            SUM(CASE WHEN t.transaction_type = 'buy' THEN t.quantity ELSE -t.quantity END) AS total_quantity
        FROM t_transactions t
        JOIN t_assets a ON t.asset_id = a.asset_id
        GROUP BY a.asset_id, a.symbol
        HAVING SUM(CASE WHEN t.transaction_type = 'buy' THEN t.quantity ELSE -t.quantity END) > 0;
    """

    holdings = _execute_query(query_holdings)
    crypto_value = 0.0

    if holdings:
        # Buscar preços em massa para reduzir falhas e latência
        symbols = [row['symbol'] for row in holdings]
        price_map = get_price_by_symbol(symbols, vs_currency='eur') or {}
        for row in holdings:
            symbol = row['symbol']
            quantity = float(row['total_quantity'])
            price = price_map.get(symbol)
            if price:
                crypto_value += quantity * float(price)
    
    total_nav = cash_balance + crypto_value
    return total_nav


def get_total_shares_in_circulation() -> float:
    """
    Calcula o total de shares em circulação (soma de todas as shares de todos os utilizadores).
    
    Returns:
        float: Total de shares no fundo
    """
    query = """
        SELECT COALESCE(SUM(shares_amount), 0) AS total_shares
        FROM t_user_shares;
    """
    
    result = _execute_query(query)
    return float(result[0]['total_shares']) if result else 0.0


def calculate_nav_per_share() -> float:
    """
    Calcula o NAV por share (preço de cada share).
    NAV per Share = Total NAV do Fundo / Total de Shares em Circulação
    
    Para o primeiro depósito (sem shares existentes), retorna 1.0 para inicializar o sistema.
    
    Returns:
        float: NAV por share
    """
    total_shares = get_total_shares_in_circulation()
    
    # Se não existem shares ainda (primeiro depósito), inicializar com NAV = 1.0
    if total_shares == 0:
        return 1.0
    
    fund_nav = calculate_fund_nav()
    nav_per_share = fund_nav / total_shares
    
    return nav_per_share


def get_user_total_shares(user_id: int) -> float:
    """
    Obtém o total de shares de um utilizador específico.
    
    Args:
        user_id: ID do utilizador
        
    Returns:
        float: Total de shares do utilizador
    """
    query = """
        SELECT COALESCE(SUM(shares_amount), 0) AS user_shares
        FROM t_user_shares
        WHERE user_id = %s;
    """
    
    result = _execute_query(query, (user_id,))
    return float(result[0]['user_shares']) if result else 0.0


def allocate_shares_on_deposit(
    user_id: int, 
    deposit_amount: float, 
    movement_date: datetime,
    notes: Optional[str] = None
) -> Dict:
    """
    Aloca shares a um utilizador quando faz um depósito.
    
    Shares atribuídas = Valor depositado / NAV por share no momento
    
    Args:
        user_id: ID do utilizador
        deposit_amount: Valor depositado em EUR
        movement_date: Data do depósito
        notes: Notas opcionais
        
    Returns:
        dict: Informação sobre a alocação (shares_allocated, nav_per_share, total_shares_after)
    """
    # Calcular NAV por share ANTES do depósito.
    # Nota: como normalmente chamamos esta função APÓS registar o depósito,
    # precisamos remover o depósito do NAV atual para obter o NAV/share correto.
    total_shares = get_total_shares_in_circulation()
    if total_shares == 0:
        nav_per_share = 1.0
    else:
        fund_nav_now = calculate_fund_nav()
        nav_per_share = (fund_nav_now - float(deposit_amount)) / total_shares
        # Salvaguarda para casos limite numéricos
        if nav_per_share <= 0:
            nav_per_share = calculate_nav_per_share()
    
    # Calcular shares a atribuir
    shares_allocated = deposit_amount / nav_per_share
    
    # Obter shares atuais do utilizador
    current_user_shares = get_user_total_shares(user_id)
    total_shares_after = current_user_shares + shares_allocated
    
    # Calcular NAV do fundo APÓS o depósito
    fund_nav_after = calculate_fund_nav()  # Já inclui o depósito recente
    
    # Inserir registo na tabela t_user_shares
    query = """
        INSERT INTO t_user_shares (
            user_id, movement_date, movement_type, amount_eur, 
            nav_per_share, shares_amount, total_shares_after, fund_nav, notes
        )
        VALUES (%s, %s, 'deposit', %s, %s, %s, %s, %s, %s);
    """
    
    _execute_query(
        query, 
        (user_id, movement_date, deposit_amount, nav_per_share, 
         shares_allocated, total_shares_after, fund_nav_after, notes)
    )
    
    return {
        'shares_allocated': shares_allocated,
        'nav_per_share': nav_per_share,
        'total_shares_after': total_shares_after,
        'fund_nav': fund_nav_after
    }


def burn_shares_on_withdrawal(
    user_id: int, 
    withdrawal_amount: float, 
    movement_date: datetime,
    notes: Optional[str] = None
) -> Dict:
    """
    Remove (queima) shares de um utilizador quando faz um levantamento.
    
    Shares removidas = Valor levantado / NAV por share no momento
    
    Args:
        user_id: ID do utilizador
        withdrawal_amount: Valor levantado em EUR (positivo)
        movement_date: Data do levantamento
        notes: Notas opcionais
        
    Returns:
        dict: Informação sobre a remoção (shares_burned, nav_per_share, total_shares_after)
    """
    # Calcular NAV por share ANTES do levantamento.
    # Como normalmente chamamos APÓS registar o levantamento (debit), somamos o valor
    # levantado ao NAV atual para obter o NAV/share do instante anterior ao movimento.
    total_shares = get_total_shares_in_circulation()
    if total_shares == 0:
        nav_per_share = 1.0
    else:
        fund_nav_now = calculate_fund_nav()
        nav_per_share = (fund_nav_now + float(withdrawal_amount)) / total_shares
        if nav_per_share <= 0:
            nav_per_share = calculate_nav_per_share()
    
    # Calcular shares a remover
    shares_burned = withdrawal_amount / nav_per_share
    
    # Obter shares atuais do utilizador
    current_user_shares = get_user_total_shares(user_id)
    total_shares_after = current_user_shares - shares_burned
    
    # Validar que o utilizador tem shares suficientes
    if total_shares_after < -0.01:  # Margem de erro por arredondamentos
        raise ValueError(
            f"Utilizador não tem shares suficientes. "
            f"Shares atuais: {current_user_shares:.6f}, "
            f"Shares a remover: {shares_burned:.6f}"
        )
    
    # Calcular NAV do fundo APÓS o levantamento
    fund_nav_after = calculate_fund_nav()  # Já reflete o levantamento
    
    # Inserir registo na tabela t_user_shares (com valor negativo)
    query = """
        INSERT INTO t_user_shares (
            user_id, movement_date, movement_type, amount_eur, 
            nav_per_share, shares_amount, total_shares_after, fund_nav, notes
        )
        VALUES (%s, %s, 'withdrawal', %s, %s, %s, %s, %s, %s);
    """
    
    _execute_query(
        query, 
        (user_id, movement_date, withdrawal_amount, nav_per_share, 
         -shares_burned, total_shares_after, fund_nav_after, notes)
    )
    
    return {
        'shares_burned': shares_burned,
        'nav_per_share': nav_per_share,
        'total_shares_after': total_shares_after,
        'fund_nav': fund_nav_after
    }


def get_user_ownership_percentage(user_id: int) -> float:
    """
    Calcula a percentagem de propriedade de um utilizador no fundo.
    
    Ownership % = (Shares do Utilizador / Total de Shares) × 100
    
    Args:
        user_id: ID do utilizador
        
    Returns:
        float: Percentagem de propriedade (0-100)
    """
    user_shares = get_user_total_shares(user_id)
    total_shares = get_total_shares_in_circulation()
    
    if total_shares == 0:
        return 0.0
    
    ownership_pct = (user_shares / total_shares) * 100
    return ownership_pct


def get_all_users_ownership() -> list:
    """
    Obtém informação de propriedade de todos os utilizadores.
    
    Returns:
        list: Lista de dicts com user_id, username, shares, ownership_pct, value_eur
    """
    query = """
        SELECT 
            u.user_id,
            u.username,
            COALESCE(SUM(s.shares_amount), 0) AS total_shares
        FROM t_users u
        LEFT JOIN t_user_shares s ON u.user_id = s.user_id
        GROUP BY u.user_id, u.username
        HAVING COALESCE(SUM(s.shares_amount), 0) > 0
        ORDER BY total_shares DESC;
    """
    
    users = _execute_query(query)
    total_shares = get_total_shares_in_circulation()
    nav_per_share = calculate_nav_per_share()
    
    result = []
    for user in users:
        user_shares = float(user['total_shares'])
        ownership_pct = (user_shares / total_shares * 100) if total_shares > 0 else 0
        value_eur = user_shares * nav_per_share
        
        result.append({
            'user_id': user['user_id'],
            'username': user['username'],
            'shares': user_shares,
            'ownership_pct': ownership_pct,
            'value_eur': value_eur
        })
    
    return result


def get_user_shares_history(user_id: int) -> list:
    """
    Obtém o histórico de movimentos de shares de um utilizador.
    
    Args:
        user_id: ID do utilizador
        
    Returns:
        list: Histórico de shares (movimento_date, type, amount, shares, nav_per_share, etc)
    """
    query = """
        SELECT 
            movement_date,
            movement_type,
            amount_eur,
            nav_per_share,
            shares_amount,
            total_shares_after,
            fund_nav,
            notes
        FROM t_user_shares
        WHERE user_id = %s
        ORDER BY movement_date DESC;
    """
    
    return _execute_query(query, (user_id,))
