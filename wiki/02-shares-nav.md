# 💎 Sistema de Shares/NAV

## Visão Geral

O sistema de shares é o **coração** do Crypto Dashboard. Garante que cada participante do fundo tem uma propriedade justa e proporcional, independentemente de quando entrou ou saiu.

### Por que Shares?

**Problema sem shares:**
```
Dia 1: João deposita €1000
Dia 30: Mercado sobe 50% → Fundo vale €1500
Dia 30: Maria deposita €1500

Como dividir o fundo agora?
- João: depositou €1000 (33%)
- Maria: depositou €1500 (50%)
❌ TOTAL = 83%? Não fecha!
❌ João não deve ter apenas 33% - ele estava desde o início!
```

**Solução com shares:**
```
Dia 1: João deposita €1000 → recebe 1000 shares (NAV/share = €1.00)
       Total fundo: €1000, Total shares: 1000
       
Dia 30: Mercado sobe 50% → Fundo vale €1500
        NAV/share = €1500 ÷ 1000 = €1.50
        
Dia 30: Maria deposita €1500 → recebe 1000 shares (€1500 ÷ €1.50)
        Total fundo: €3000, Total shares: 2000
        
Propriedade:
✅ João: 1000 shares = 50% do fundo = €1500
✅ Maria: 1000 shares = 50% do fundo = €1500
✅ TOTAL: 100% 🎯
```

## Conceitos Fundamentais

### NAV (Net Asset Value)

**Definição**: Valor líquido total do fundo

**Fórmula**:
```
NAV Total = Caixa Disponível + Valor das Holdings em Cripto
```

**Componentes**:

1. **Caixa Disponível**:
   ```
   Caixa = Σ Depósitos 
         - Σ Levantamentos 
         - Σ (Compras + Fees de Compra)
         + Σ (Vendas - Fees de Venda)
   ```

2. **Valor das Holdings**:
   ```
   Para cada ativo:
       Holdings[ativo] = Σ Quantidades Compradas - Σ Quantidades Vendidas
       Valor[ativo] = Holdings[ativo] × Preço Atual
   
   Total Holdings = Σ Valor[todos os ativos]
   ```

**Implementação**:
```python
def calculate_fund_nav() -> float:
    # 1. Calcular caixa (excluindo admins)
    query_cash = """
        WITH capital AS (
            SELECT 
                SUM(COALESCE(credit, 0)) AS deposits,
                SUM(COALESCE(debit, 0)) AS withdrawals
            FROM t_user_capital_movements uc
            JOIN t_users u ON u.user_id = uc.user_id
            WHERE u.is_admin = FALSE
        ),
        trades AS (
            SELECT 
                SUM(CASE WHEN transaction_type = 'buy' 
                    THEN price_eur * quantity + fee_eur 
                    ELSE 0 END) AS spent,
                SUM(CASE WHEN transaction_type = 'sell' 
                    THEN (price_eur * quantity) - fee_eur 
                    ELSE 0 END) AS received
            FROM t_transactions
        )
        SELECT (c.deposits - c.withdrawals - t.spent + t.received) AS cash
        FROM capital c, trades t;
    """
    
    cash_balance = execute_query(query_cash)[0]['cash']
    
    # 2. Calcular valor de holdings
    holdings = get_holdings()  # {symbol: quantity}
    prices = get_price_by_symbol(holdings.keys(), vs_currency='eur')
    
    crypto_value = 0.0
    for symbol, quantity in holdings.items():
        if quantity > 0 and prices.get(symbol):
            crypto_value += quantity * float(prices[symbol])
    
    return cash_balance + crypto_value
```

### NAV por Share

**Definição**: Preço de cada share do fundo

**Fórmula**:
```
NAV/share = NAV Total do Fundo ÷ Total de Shares em Circulação
```

**Caso Especial - Primeiro Depósito**:
```python
if total_shares == 0:
    return 1.0  # Inicializa com NAV/share = €1.00
```

**Evolução**:
- 📈 **Mercado sobe**: NAV/share aumenta
- 📉 **Mercado desce**: NAV/share diminui
- 💰 **Novo depósito**: NAV/share mantém-se (shares proporcionais)
- 💸 **Levantamento**: NAV/share mantém-se (queima shares proporcionais)

### Total Shares em Circulação

**Definição**: Soma de todas as shares de todos os utilizadores

**Fórmula**:
```
Total Shares = Σ shares_amount (de todos os registos em t_user_shares)
```

**Implementação**:
```python
def get_total_shares_in_circulation() -> float:
    query = """
        SELECT COALESCE(SUM(shares_amount), 0) AS total_shares
        FROM t_user_shares;
    """
    return execute_query(query)[0]['total_shares']
```

**Características**:
- Depósitos: adicionam shares (positivo)
- Levantamentos: removem shares (negativo)
- Transações de cripto: não afetam total shares

## Operações

### 1. Depósito (Allocate Shares)

**Fluxo**:
```
1. Utilizador deposita X euros
2. Sistema calcula NAV/share ANTES do depósito
3. Shares atribuídas = X ÷ NAV/share
4. Registo criado em t_user_shares
5. Total shares aumenta
```

**Implementação**:
```python
def allocate_shares_on_deposit(
    user_id: int, 
    deposit_amount: float, 
    movement_date: datetime,
    notes: Optional[str] = None
) -> Dict:
    # Calcular NAV/share ANTES do depósito
    total_shares = get_total_shares_in_circulation()
    
    if total_shares == 0:
        # Primeiro depósito
        nav_per_share = 1.0
    else:
        # NAV antes = (NAV atual - depósito) ÷ shares existentes
        fund_nav_now = calculate_fund_nav()
        nav_per_share = (fund_nav_now - deposit_amount) / total_shares
    
    # Calcular shares
    shares_allocated = deposit_amount / nav_per_share
    
    # Obter shares atuais do utilizador
    current_user_shares = get_user_total_shares(user_id)
    total_shares_after = current_user_shares + shares_allocated
    
    # NAV após o depósito
    fund_nav_after = calculate_fund_nav()
    
    # Inserir registo
    query = """
        INSERT INTO t_user_shares (
            user_id, movement_date, movement_type, amount_eur, 
            nav_per_share, shares_amount, total_shares_after, fund_nav, notes
        )
        VALUES (%s, %s, 'deposit', %s, %s, %s, %s, %s, %s);
    """
    execute_query(query, (
        user_id, movement_date, deposit_amount, nav_per_share, 
        shares_allocated, total_shares_after, fund_nav_after, notes
    ))
    
    return {
        'shares_allocated': shares_allocated,
        'nav_per_share': nav_per_share,
        'total_shares_after': total_shares_after,
        'fund_nav': fund_nav_after
    }
```

**Exemplo Prático**:
```
Situação inicial:
- NAV Total = €10,000
- Total Shares = 5,000
- NAV/share = €2.00

João deposita €4,000:
1. NAV/share (antes) = (€10,000 - €4,000) ÷ 5,000 = €1.20
   ❌ Errado! Não podemos subtrair porque o depósito já foi registado
   
Correção: Esta função é chamada APÓS inserir em t_user_capital_movements
Então o NAV atual já inclui o depósito novo.

1. NAV/share (antes) = (€14,000 [atual] - €4,000 [novo]) ÷ 5,000 = €2.00 ✅
2. Shares para João = €4,000 ÷ €2.00 = 2,000 shares
3. Novo total = 5,000 + 2,000 = 7,000 shares
4. João agora tem 2,000 shares = 28.57% do fundo

Verificação:
- NAV Total = €14,000
- Total Shares = 7,000
- NAV/share = €14,000 ÷ 7,000 = €2.00 ✅ (mantém-se)
```

### 2. Levantamento (Burn Shares)

**Fluxo**:
```
1. Utilizador levanta X euros
2. Sistema calcula NAV/share ANTES do levantamento
3. Shares a queimar = X ÷ NAV/share
4. Validação: utilizador tem shares suficientes?
5. Registo negativo criado em t_user_shares
6. Total shares diminui
```

**Implementação**:
```python
def burn_shares_on_withdrawal(
    user_id: int, 
    withdrawal_amount: float, 
    movement_date: datetime,
    notes: Optional[str] = None
) -> Dict:
    # Calcular NAV/share ANTES do levantamento
    total_shares = get_total_shares_in_circulation()
    
    if total_shares == 0:
        raise ValueError("Não há shares para queimar")
    
    # NAV antes = (NAV atual + levantamento) ÷ shares existentes
    # (porque o levantamento já foi registado como debit)
    fund_nav_now = calculate_fund_nav()
    nav_per_share = (fund_nav_now + withdrawal_amount) / total_shares
    
    # Calcular shares a remover
    shares_burned = withdrawal_amount / nav_per_share
    
    # Validar shares suficientes
    current_user_shares = get_user_total_shares(user_id)
    total_shares_after = current_user_shares - shares_burned
    
    if total_shares_after < -0.01:  # Margem para arredondamento
        raise ValueError(
            f"Shares insuficientes. "
            f"Tem: {current_user_shares:.6f}, "
            f"Precisa: {shares_burned:.6f}"
        )
    
    # NAV após o levantamento
    fund_nav_after = calculate_fund_nav()
    
    # Inserir registo (negativo)
    query = """
        INSERT INTO t_user_shares (
            user_id, movement_date, movement_type, amount_eur, 
            nav_per_share, shares_amount, total_shares_after, fund_nav, notes
        )
        VALUES (%s, %s, 'withdrawal', %s, %s, %s, %s, %s, %s);
    """
    execute_query(query, (
        user_id, movement_date, withdrawal_amount, nav_per_share, 
        -shares_burned,  # ← NEGATIVO
        total_shares_after, fund_nav_after, notes
    ))
    
    return {
        'shares_burned': shares_burned,
        'nav_per_share': nav_per_share,
        'total_shares_after': total_shares_after,
        'fund_nav': fund_nav_after
    }
```

**Exemplo Prático**:
```
Situação:
- Maria tem 1,000 shares de 5,000 totais (20%)
- NAV Total = €10,000
- NAV/share = €2.00

Maria levanta €800:
1. NAV/share (antes) = (€9,200 [após debit] + €800) ÷ 5,000 = €2.00
2. Shares a queimar = €800 ÷ €2.00 = 400 shares
3. Maria fica com 1,000 - 400 = 600 shares
4. Total shares = 5,000 - 400 = 4,600

Verificação:
- Maria: 600 shares ÷ 4,600 = 13.04% ✅ (teve menos % porque levantou)
- NAV Total = €9,200
- NAV/share = €9,200 ÷ 4,600 = €2.00 ✅ (mantém-se)
```

### 3. Transações de Cripto

**Importante**: Compras e vendas de cripto **NÃO afetam shares**!

**Porquê?**
- Compra: Trocamos caixa por cripto → NAV mantém-se → shares mantêm-se
- Venda: Trocamos cripto por caixa → NAV mantém-se → shares mantêm-se
- Apenas variações de preço de mercado mudam o NAV/share

**Exemplo**:
```
Antes:
- Caixa: €5,000
- Holdings: 0
- NAV Total: €5,000
- Total Shares: 5,000
- NAV/share: €1.00

Compramos 100 ADA a €0.50 (total €50):
- Caixa: €4,950 (gastamos €50)
- Holdings: 100 ADA × €0.50 = €50
- NAV Total: €4,950 + €50 = €5,000 ✅ (igual)
- Total Shares: 5,000 ✅ (igual)
- NAV/share: €1.00 ✅ (igual)

ADA sobe para €1.00:
- Caixa: €4,950
- Holdings: 100 ADA × €1.00 = €100 📈
- NAV Total: €4,950 + €100 = €5,050
- Total Shares: 5,000 (não muda)
- NAV/share: €5,050 ÷ 5,000 = €1.01 📈 (sobe!)
```

## Ownership (Propriedade)

### Cálculo de Ownership %

**Fórmula**:
```
Ownership % = (Shares do Utilizador ÷ Total Shares) × 100
```

**Implementação**:
```python
def get_user_ownership_percentage(user_id: int) -> float:
    user_shares = get_user_total_shares(user_id)
    total_shares = get_total_shares_in_circulation()
    
    if total_shares == 0:
        return 0.0
    
    return (user_shares / total_shares) * 100
```

### Valor em EUR do Utilizador

**Fórmula**:
```
Valor do Utilizador = Shares do Utilizador × NAV/share
```

**Exemplo**:
```python
def get_user_value(user_id: int) -> float:
    user_shares = get_user_total_shares(user_id)
    nav_per_share = calculate_nav_per_share()
    return user_shares * nav_per_share
```

### Todos os Utilizadores

**Implementação**:
```python
def get_all_users_ownership() -> List[Dict]:
    # Buscar todos users com shares
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
    users = execute_query(query)
    
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
```

## Histórico de Shares

### Tabela t_user_shares

**Estrutura**:
```sql
CREATE TABLE t_user_shares (
    share_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES t_users(user_id),
    movement_date TIMESTAMP NOT NULL,
    movement_type VARCHAR(20) NOT NULL,  -- 'deposit' | 'withdrawal'
    amount_eur NUMERIC(15, 2) NOT NULL,   -- Valor do movimento
    nav_per_share NUMERIC(15, 6) NOT NULL, -- NAV/share no momento
    shares_amount NUMERIC(15, 6) NOT NULL, -- Positivo ou negativo
    total_shares_after NUMERIC(15, 6) NOT NULL, -- Acumulado do user
    fund_nav NUMERIC(15, 2) NOT NULL,     -- NAV total do fundo
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Características**:
- ✅ **Imutável**: Registos nunca são alterados (audit trail)
- ✅ **Completo**: Cada movimento tem contexto completo (NAV, shares, etc)
- ✅ **Auditável**: Pode-se reconstruir histórico completo

**Exemplo de Dados**:
```
share_id | user_id | movement_date | type       | amount_eur | nav_per_share | shares_amount | total_shares_after | fund_nav
---------|---------|---------------|------------|------------|---------------|---------------|--------------------|---------
1        | 3       | 2025-01-01    | deposit    | 500.00     | 1.0000        | 500.000000    | 500.000000         | 500.00
2        | 4       | 2025-01-15    | deposit    | 300.00     | 1.2000        | 250.000000    | 250.000000         | 900.00
3        | 3       | 2025-02-01    | deposit    | 200.00     | 1.1500        | 173.913043    | 673.913043         | 1100.00
4        | 4       | 2025-03-01    | withdrawal | 150.00     | 1.3000        | -115.384615   | 134.615385         | 950.00
```

### Consultar Histórico

**Por Utilizador**:
```python
def get_user_shares_history(user_id: int) -> List[Dict]:
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
    return execute_query(query, (user_id,))
```

**Output**:
```python
[
    {
        'movement_date': datetime(2025, 3, 1),
        'movement_type': 'withdrawal',
        'amount_eur': 150.00,
        'nav_per_share': 1.30,
        'shares_amount': -115.384615,
        'total_shares_after': 134.615385,
        'fund_nav': 950.00,
        'notes': None
    },
    # ...
]
```

## Casos Especiais

### 1. Primeiro Depósito do Fundo

**Situação**: Ninguém tem shares ainda

**Comportamento**:
```python
if total_shares == 0:
    nav_per_share = 1.0  # Inicializa com €1.00
```

**Exemplo**:
```
João é o primeiro → deposita €1,000
- NAV/share = €1.00 (fixo)
- Shares para João = €1,000 ÷ €1.00 = 1,000 shares
- João tem 100% do fundo
```

### 2. Levantamento Total

**Situação**: Utilizador levanta tudo o que tem

**Comportamento**:
```python
# Sistema calcula shares exatas
shares_to_burn = withdrawal_amount / nav_per_share

# Utilizador fica com 0 shares (ou valor muito próximo)
```

**Exemplo**:
```
Maria tem 500 shares, NAV/share = €2.00 → Valor = €1,000

Maria levanta €1,000:
- Shares queimadas = €1,000 ÷ €2.00 = 500 shares
- Maria fica com 0.000000 shares ✅
```

### 3. Arredondamentos

**Problema**: Divisões podem criar decimais infinitos

**Solução**: Usamos `NUMERIC(15, 6)` (6 casas decimais)

**Tolerância**:
```python
if total_shares_after < -0.01:  # Margem de ±0.01 shares
    raise ValueError("Shares insuficientes")
```

### 4. Mercado em Queda

**Situação**: NAV/share desce (mercado bearish)

**Comportamento**:
```
Antes: NAV/share = €2.00
Mercado cai 50%
Depois: NAV/share = €1.00

Impacto:
- Total shares: não muda
- Ownership %: não muda
- Valor em EUR: cai 50% para todos ⚠️
```

**Novo depósito**:
```
Pedro deposita €1,000 com NAV/share = €1.00
- Recebe 1,000 shares (o dobro do que receberia a €2.00!)
- Quando mercado recuperar, Pedro beneficia proporcionalmente
```

## Verificação de Integridade

### Testes de Consistência

```python
def validate_nav_consistency():
    """Verifica se NAV = cash + crypto"""
    nav = calculate_fund_nav()
    
    cash = get_cash_balance()
    crypto_value = get_crypto_holdings_value()
    
    assert abs(nav - (cash + crypto_value)) < 0.01, "NAV inconsistente!"

def validate_shares_consistency():
    """Verifica se sum(user shares) = total shares"""
    total_from_users = sum(get_user_total_shares(uid) for uid in all_user_ids)
    total_in_circulation = get_total_shares_in_circulation()
    
    assert abs(total_from_users - total_in_circulation) < 0.01, "Shares inconsistentes!"

def validate_ownership_sums_100():
    """Verifica se soma de ownership = 100%"""
    users = get_all_users_ownership()
    total_pct = sum(u['ownership_pct'] for u in users)
    
    assert abs(total_pct - 100.0) < 0.01, "Ownership não soma 100%!"
```

### Queries de Auditoria

```sql
-- Ver discrepâncias entre valor calculado e valor registado
SELECT 
    user_id,
    SUM(shares_amount) AS calculated_shares,
    (SELECT total_shares_after FROM t_user_shares 
     WHERE user_id = us.user_id 
     ORDER BY movement_date DESC LIMIT 1) AS last_recorded_total,
    SUM(shares_amount) - 
    (SELECT total_shares_after FROM t_user_shares 
     WHERE user_id = us.user_id 
     ORDER BY movement_date DESC LIMIT 1) AS difference
FROM t_user_shares us
GROUP BY user_id
HAVING ABS(SUM(shares_amount) - 
    (SELECT total_shares_after FROM t_user_shares 
     WHERE user_id = us.user_id 
     ORDER BY movement_date DESC LIMIT 1)) > 0.01;
```

## Boas Práticas

### ✅ DO

- Sempre chamar `allocate_shares_on_deposit()` **APÓS** inserir em `t_user_capital_movements`
- Sempre chamar `burn_shares_on_withdrawal()` **APÓS** inserir debit
- Validar shares suficientes antes de levantamentos
- Usar transações de BD para garantir atomicidade
- Preservar todo o histórico em `t_user_shares`
- Testar cálculos com arredondamentos

### ❌ DON'T

- ❌ Nunca alterar registos em `t_user_shares` (imutável)
- ❌ Nunca permitir `total_shares_after` negativo
- ❌ Nunca calcular NAV incluindo admins
- ❌ Nunca usar float para valores monetários (usar Decimal)
- ❌ Nunca assumir que NAV/share é fixo

## FAQ

**Q: O que acontece se o fundo chegar a NAV = €0?**  
A: NAV/share seria €0, mas sistemas normalmente param operações antes disso (ex: stop-loss automático).

**Q: Posso transferir shares entre utilizadores?**  
A: Não implementado atualmente. Precisaria de nova funcionalidade e tipo de movimento.

**Q: Como funciona se houver taxas de gestão?**  
A: Taxas deduziriam caixa do fundo → NAV diminui → NAV/share diminui → todos pagam proporcionalmente.

**Q: E se um utilizador tiver shares negativas?**  
A: Impossível. Sistema valida antes de queimar shares.

**Q: Shares expiram?**  
A: Não. Ownership é perpétuo até levantamento.

---

**Anterior**: [← Arquitetura Técnica](01-arquitetura.md)  
**Próximo**: [Snapshots e Preços →](03-snapshots-precos.md)
