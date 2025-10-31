# Sistema de Shares - Guia de Implementação

## ✅ Ficheiros Criados/Modificados

### 1. Schema de Base de Dados
- ✅ `database/migrations/007_add_user_shares.sql` - Migration para criar tabela t_user_shares
- ✅ `database/tables.sql` - Adicionada t_user_shares para novos DBs
- ✅ `services/shares.py` - Módulo completo para gestão de shares

## 📋 Próximos Passos

### PASSO 1: Executar Migration na Base de Dados

**Opção A - Via DBeaver:**
1. Abrir DBeaver e conectar à base de dados CryptoDashboard
2. Abrir o ficheiro `database/migrations/007_add_user_shares.sql`
3. Executar todo o script (Ctrl+Enter ou botão Execute)
4. Verificar que a tabela `t_user_shares` foi criada com sucesso

**Opção B - Via psql (linha de comandos):**
```powershell
psql -U postgres -d cryptodashboard -f "C:\CryptoDashboard\database\migrations\007_add_user_shares.sql"
```

### PASSO 2: Integrar Share Allocation nos Depósitos

Modificar o código onde são registados depósitos para chamar `allocate_shares_on_deposit()`.

**Localização provável:** Ficheiro que gere a tabela `t_user_capital_movements` ou página de utilizadores.

**Código a adicionar após inserir movimento de capital:**

```python
from services.shares import allocate_shares_on_deposit
from datetime import datetime

# Após inserir o depósito em t_user_capital_movements
if movement_type == 'deposit':
    try:
        share_info = allocate_shares_on_deposit(
            user_id=user_id,
            deposit_amount=amount_eur,
            movement_date=datetime.now(),
            notes=f"Depósito de {amount_eur}€"
        )
        
        st.success(
            f"✅ Depósito registado com sucesso! "
            f"Shares atribuídas: {share_info['shares_allocated']:.6f} "
            f"(NAV/share: {share_info['nav_per_share']:.2f}€)"
        )
    except Exception as e:
        st.error(f"Erro ao alocar shares: {str(e)}")
```

### PASSO 3: Integrar Share Burning nos Levantamentos

**Código a adicionar após inserir levantamento em t_user_capital_movements:**

```python
from services.shares import burn_shares_on_withdrawal
from datetime import datetime

# Após inserir o levantamento em t_user_capital_movements
if movement_type == 'withdrawal':
    try:
        share_info = burn_shares_on_withdrawal(
            user_id=user_id,
            withdrawal_amount=amount_eur,
            movement_date=datetime.now(),
            notes=f"Levantamento de {amount_eur}€"
        )
        
        st.success(
            f"✅ Levantamento registado com sucesso! "
            f"Shares removidas: {share_info['shares_burned']:.6f} "
            f"(NAV/share: {share_info['nav_per_share']:.2f}€)"
        )
    except ValueError as e:
        st.error(f"❌ Erro: {str(e)}")
```

### PASSO 4: Adicionar UI de Ownership na Análise de Portfolio

Em `pages/portfolio_analysis.py`, adicionar nova secção após "Composição do Portfólio":

```python
from services.shares import (
    get_all_users_ownership, 
    calculate_nav_per_share, 
    get_total_shares_in_circulation
)
import pandas as pd

# ... código existente ...

st.header("👥 Propriedade do Fundo")

# Métricas principais
col1, col2, col3 = st.columns(3)

nav_per_share = calculate_nav_per_share()
total_shares = get_total_shares_in_circulation()
fund_nav = nav_per_share * total_shares if total_shares > 0 else 0

with col1:
    st.metric("NAV por Share", f"{nav_per_share:.4f}€")
with col2:
    st.metric("Total Shares em Circulação", f"{total_shares:.2f}")
with col3:
    st.metric("NAV Total do Fundo", f"{fund_nav:,.2f}€")

# Tabela de ownership
ownership_data = get_all_users_ownership()

if ownership_data:
    df_ownership = pd.DataFrame(ownership_data)
    df_ownership['ownership_pct'] = df_ownership['ownership_pct'].apply(lambda x: f"{x:.2f}%")
    df_ownership['shares'] = df_ownership['shares'].apply(lambda x: f"{x:.6f}")
    df_ownership['value_eur'] = df_ownership['value_eur'].apply(lambda x: f"{x:,.2f}€")
    
    df_ownership.columns = ['User ID', 'Username', 'Shares', 'Propriedade (%)', 'Valor (EUR)']
    
    st.dataframe(
        df_ownership[['Username', 'Shares', 'Propriedade (%)', 'Valor (EUR)']], 
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("Nenhum utilizador com shares no momento.")
```

### PASSO 5: (Opcional) Histórico de Shares por Utilizador

Adicionar em página de settings ou perfil do utilizador:

```python
from services.shares import get_user_shares_history
import pandas as pd

user_id = 1  # ou st.session_state.user_id

st.subheader("📜 Histórico de Shares")

history = get_user_shares_history(user_id)

if history:
    df_history = pd.DataFrame(history)
    df_history['movement_date'] = pd.to_datetime(df_history['movement_date']).dt.strftime('%Y-%m-%d %H:%M')
    df_history['movement_type'] = df_history['movement_type'].map({
        'deposit': '➕ Depósito',
        'withdrawal': '➖ Levantamento'
    })
    
    df_history.columns = [
        'Data', 'Tipo', 'Valor (EUR)', 'NAV/Share', 
        'Shares', 'Total Shares Após', 'NAV do Fundo', 'Notas'
    ]
    
    st.dataframe(df_history, use_container_width=True, hide_index=True)
else:
    st.info("Sem histórico de shares.")
```

## 🧮 Como Funciona o Sistema

### Exemplo Prático: Diogo vs Catarina

**Janeiro - Diogo deposita 200€:**
- Primeiro depósito → NAV/share inicializa em 1.0€
- Shares atribuídas: 200€ / 1.0€ = **200 shares**
- Diogo: 200 shares (100% do fundo)

**Admin compra 180€ de ADA:**
- Fund NAV: 20€ (caixa) + 200€ (cripto valorizado) = 220€
- Total shares: 200
- NAV/share: 220€ / 200 = **1.10€**

**Fevereiro - Catarina deposita 200€:**
- NAV/share no momento: 1.10€
- Shares atribuídas: 200€ / 1.10€ = **181.82 shares**
- Fund NAV: 420€ (20 caixa + 200 cripto + 200 novo depósito)
- Total shares: 200 + 181.82 = 381.82

**Propriedade final:**
- Diogo: 200 / 381.82 = **52.38%** ✅
- Catarina: 181.82 / 381.82 = **47.62%** ✅

Ambos depositaram 200€, mas Diogo tem maior percentagem porque entrou quando o NAV era mais baixo!

## ⚠️ Pontos Críticos

1. **Ordem das operações:** Sempre registar em `t_user_capital_movements` ANTES de alocar/queimar shares
2. **Transações atómicas:** Depósito + share allocation devem estar na mesma transação DB
3. **Validação:** Antes de withdrawal, verificar se user tem shares suficientes
4. **Precisão:** Usar NUMERIC(18,6) para shares (6 casas decimais)
5. **Primeiro depósito:** Sistema inicializa automaticamente com NAV = 1.0

## 🔍 Verificações Pós-Implementação

```sql
-- Verificar total de shares vs NAV
SELECT 
    SUM(shares_amount) AS total_shares,
    (SELECT fund_nav FROM t_user_shares ORDER BY movement_date DESC LIMIT 1) AS ultimo_nav
FROM t_user_shares;

-- Ver ownership atual
SELECT 
    u.username,
    SUM(s.shares_amount) AS shares,
    ROUND(SUM(s.shares_amount) / (SELECT SUM(shares_amount) FROM t_user_shares) * 100, 2) AS ownership_pct
FROM t_users u
LEFT JOIN t_user_shares s ON u.user_id = s.user_id
GROUP BY u.user_id, u.username
HAVING SUM(s.shares_amount) > 0;
```

## 📞 Próximo Checkpoint

Depois de executar a migration (Passo 1), avisa para integrar nos fluxos de depósito/levantamento!
