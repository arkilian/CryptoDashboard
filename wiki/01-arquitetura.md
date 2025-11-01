# 🏗️ Arquitetura Técnica

## Visão Geral

O Crypto Dashboard é construído com uma arquitetura em camadas, separando claramente a interface do utilizador, lógica de negócio, acesso a dados e integrações externas.

```
┌─────────────────────────────────────────────────┐
│         Frontend (Streamlit UI)                 │
│  app.py, pages/*, components                    │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│         Services (Business Logic)               │
│  services/shares.py                             │
│  services/snapshots.py                          │
│  services/coingecko.py                          │
│  services/calculations.py                       │
│  services/fees.py                               │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│         Database Layer                          │
│  database/connection.py                         │
│  database/users.py                              │
│  database/portfolio.py                          │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│         PostgreSQL Database                     │
│  Tables, Indexes, Constraints                   │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│         External APIs                           │
│  CoinGecko API (preços)                         │
└─────────────────────────────────────────────────┘
```

## Stack Tecnológico

### Backend
- **Python 3.10+**: Linguagem principal
- **Streamlit**: Framework web para UI interativa
- **PostgreSQL**: Base de dados relacional
- **SQLAlchemy**: ORM e abstração de queries
- **psycopg2**: Driver PostgreSQL
- **bcrypt**: Hash de passwords

### Frontend
- **Streamlit Components**: UI widgets nativos
- **Plotly**: Visualizações interativas (gráficos, charts)
- **Pandas**: Manipulação de dados e dataframes
- **datetime/dateutil**: Gestão de datas

### Integrações
- **CoinGecko API**: Preços de criptomoedas em tempo real e históricos
- **Requests**: Cliente HTTP para APIs externas

## Estrutura de Diretórios

```
CryptoDashboard/
├── app.py                          # Entry point da aplicação
├── config.py                       # Configurações globais
├── requirements.txt                # Dependências Python
│
├── auth/                           # Autenticação e sessão
│   ├── login.py                    # Lógica de login
│   ├── register.py                 # Registo de utilizadores
│   └── session_manager.py          # Gestão de sessão Streamlit
│
├── database/                       # Camada de acesso a dados
│   ├── connection.py               # Pool de conexões PostgreSQL
│   ├── users.py                    # Queries relacionadas a utilizadores
│   ├── portfolio.py                # Queries de portfólio
│   ├── tables.sql                  # Schema inicial da BD
│   └── migrations/                 # Migrações de schema
│       ├── 001_*.sql
│       ├── 007_add_user_shares.sql
│       └── ...
│
├── pages/                          # Páginas da aplicação (routing)
│   ├── analytics.py                # Página de análise (legacy)
│   ├── portfolio.py                # Gestão de portfólio
│   ├── portfolio_analysis.py       # Dashboard de análise completo
│   ├── settings.py                 # Configurações
│   └── users.py                    # Gestão de utilizadores (admin)
│
├── services/                       # Lógica de negócio
│   ├── calculations.py             # Cálculos financeiros
│   ├── coingecko.py                # Cliente CoinGecko API
│   ├── fees.py                     # Gestão de taxas
│   ├── minswap.py                  # Integração MinSwap
│   ├── shares.py                   # Sistema de shares/NAV ⭐
│   └── snapshots.py                # Cache de preços históricos ⭐
│
├── utils/                          # Utilitários
│   ├── formatters.py               # Formatação de números/datas
│   └── security.py                 # Funções de segurança
│
└── wiki/                           # Documentação
    ├── 01-arquitetura.md
    ├── 02-shares-nav.md
    └── ...
```

## Base de Dados

### Schema Principal

#### Tabelas de Utilizadores
```sql
-- Autenticação e perfil base
t_users
├── user_id (PK)
├── username (unique)
├── password_hash
├── email (unique)
└── is_admin (boolean)

-- Perfil detalhado
t_user_profile
├── profile_id (PK)
├── user_id (FK → t_users)
├── full_name
├── birth_date
├── gender
└── address
```

#### Tabelas de Capital
```sql
-- Movimentos de capital (depósitos/levantamentos)
t_user_capital_movements
├── movement_id (PK)
├── user_id (FK → t_users)
├── movement_date
├── credit (depósito)
├── debit (levantamento)
└── notes

-- Sistema de shares (ownership) ⭐
t_user_shares
├── share_id (PK)
├── user_id (FK → t_users)
├── movement_date
├── movement_type ('deposit' | 'withdrawal')
├── amount_eur
├── nav_per_share (preço da share no momento)
├── shares_amount (positivo ou negativo)
├── total_shares_after (acumulado do user)
├── fund_nav (NAV total do fundo)
└── notes
```

#### Tabelas de Ativos e Transações
```sql
-- Ativos disponíveis
t_assets
├── asset_id (PK)
├── symbol (e.g., 'BTC', 'ETH', 'EUR')
├── name
├── chain
├── coingecko_id
└── is_stablecoin (BOOLEAN)

-- Exchanges e Contas
t_exchanges
├── exchange_id (PK)
├── name
└── category

t_exchange_accounts
├── account_id (PK)
├── exchange_id (FK → t_exchanges)
├── user_id (FK → t_users)
├── name (rótulo da conta)
└── account_category (ex.: Spot, Earn, Wallet)

-- Transações (Modelo V2)
t_transactions
├── transaction_id (PK)
├── transaction_date (TIMESTAMPTZ)
├── transaction_type CHECK (
│   'buy','sell','deposit','withdrawal','swap','transfer',
│   'stake','unstake','reward','lend','borrow','repay','liquidate'
│)
│
├── -- Campos legacy (retrocompat; agora NULLABLE)
├── asset_id (FK → t_assets)
├── quantity
├── price_eur
├── total_eur
├── fee_eur DEFAULT 0
│
├── -- Conta principal associada (quando aplicável)
├── account_id (FK → t_exchange_accounts)
│
├── -- Campos V2 (multi-asset / multi-conta)
├── from_asset_id (FK → t_assets)
├── to_asset_id   (FK → t_assets)
├── from_quantity
├── to_quantity
├── from_account_id (FK → t_exchange_accounts)
├── to_account_id   (FK → t_exchange_accounts)
├── fee_asset_id    (FK → t_assets)
├── fee_quantity DEFAULT 0
│
├── executed_by (FK → t_users)
└── notes

-- Índices recomendados
CREATE INDEX IF NOT EXISTS idx_transactions_date ON t_transactions(transaction_date DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON t_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_transactions_account ON t_transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_from_asset ON t_transactions(from_asset_id);
CREATE INDEX IF NOT EXISTS idx_transactions_to_asset ON t_transactions(to_asset_id);
CREATE INDEX IF NOT EXISTS idx_transactions_from_account ON t_transactions(from_account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_to_account ON t_transactions(to_account_id);
```

Notas:
- EUR é tratado como um asset em `t_assets` com `is_stablecoin=TRUE`.
- Existe a exchange especial "Banco" (categoria FIAT) para movimentos em EUR fora das exchanges.
- A coluna `name` foi adicionada a `t_exchange_accounts` para identificar cada conta (ex.: Spot, Earn, Wallet).
- As colunas legacy foram tornadas NULLABLE e continuam suportadas para compatibilidade.
- A migração automática é aplicada no arranque (ver `apply_transaction_model_v2()` e `app.py`).

#### Cache de Preços ⭐
```sql
-- Snapshots de preços históricos
t_price_snapshots
├── snapshot_id (PK)
├── asset_id (FK → t_assets)
├── snapshot_date
├── price
├── vs_currency ('eur', 'usd', etc)
└── created_at

-- Index para busca rápida
CREATE INDEX idx_price_snapshots_lookup 
ON t_price_snapshots(asset_id, snapshot_date, vs_currency);
```

### Relacionamentos

```
t_users (1) ──────→ (N) t_user_profile
   │
   ├──────→ (N) t_user_capital_movements
   ├──────→ (N) t_user_shares ⭐
   └──────→ (N) t_transactions
                       │
                       └──→ (1) t_assets
                                  │
                                  └──→ (N) t_price_snapshots ⭐
```

## Componentes Principais

### 1. Sistema de Autenticação

**Localização**: `auth/`

**Fluxo**:
1. Utilizador submete credenciais
2. `login.py` valida contra `t_users` (bcrypt hash)
3. `session_manager.py` cria sessão Streamlit
4. Sessão armazena: `user_id`, `username`, `is_admin`
5. Decorator `@require_auth` protege páginas

**Segurança**:
- Passwords nunca armazenadas em plain text
- bcrypt com salt automático
- Sessão server-side do Streamlit
- Validação em todas as páginas protegidas

### 2. Gestão de Conexões PostgreSQL

**Localização**: `database/connection.py`

**Pool de Conexões**:
```python
# Singleton pattern
def get_connection() -> connection:
    """Retorna conexão do pool"""
    
def return_connection(conn) -> None:
    """Devolve conexão ao pool"""
    
def get_engine() -> Engine:
    """Retorna SQLAlchemy engine para pandas"""
```

**Boas Práticas**:
- Sempre usar `try/finally` com `return_connection()`
- Usar `get_engine()` para queries pandas read_sql
- Transações explícitas com `conn.commit()` ou `conn.rollback()`

### 3. Serviço de Shares/NAV ⭐

**Localização**: `services/shares.py`

**Funções Core**:
```python
calculate_fund_nav() -> float
    # NAV = Caixa + Holdings
    # Exclui utilizadores admin
    # Usa preços atuais

calculate_nav_per_share() -> float
    # NAV/share = NAV Total ÷ Total Shares

allocate_shares_on_deposit(user_id, amount, date)
    # Calcula shares = amount ÷ NAV/share
    # Insere em t_user_shares (positivo)
    
burn_shares_on_withdrawal(user_id, amount, date)
    # Calcula shares = amount ÷ NAV/share
    # Insere em t_user_shares (negativo)
    # Valida shares suficientes

get_all_users_ownership() -> List[Dict]
    # Lista todos utilizadores com shares
    # Calcula ownership % e valor EUR
```

**Características**:
- Cálculo always fresh (não usa cache)
- Exclusão de admins nos movimentos de capital
- Validação de saldo de shares antes de queimar
- Histórico completo preservado em t_user_shares

### 4. Sistema de Snapshots de Preços ⭐

**Localização**: `services/snapshots.py`

**Estratégia DB-First**:
```python
get_historical_price(asset_id, date) -> Optional[float]:
    # 1. Buscar em t_price_snapshots
    if found:
        return cached_price
    
    # 2. Não encontrado → Buscar na API CoinGecko
    price = fetch_from_coingecko(asset_id, date)
    
    # 3. Armazenar para futuro
    save_to_t_price_snapshots(asset_id, date, price)
    
    # 4. Rate limiting
    time.sleep(2)  # Evitar 429 Too Many Requests
    
    return price
```

**Funções Auxiliares**:
```python
get_historical_prices_bulk(asset_ids, date)
    # Batch query na BD
    # Fetch individual apenas para missing
    
get_historical_prices_by_symbol(symbols, date)
    # Mapeia símbolos → asset_ids
    # Chama bulk fetch
    # Session cache para evitar duplicatas
```

**Cache em Camadas**:
1. **Session Cache**: Dicionário em memória durante execução
2. **Database Cache**: `t_price_snapshots` (persistente)
3. **API Call**: Último recurso com rate limiting

### 5. Cliente CoinGecko

**Localização**: `services/coingecko.py`

**Endpoints Utilizados**:
```python
# Preços atuais
GET /simple/price
    ?ids=bitcoin,ethereum,cardano
    &vs_currencies=eur

# Preços históricos
GET /coins/{id}/history
    ?date=31-10-2025  # DD-MM-YYYY
```

**Características**:
- Retry com exponential backoff (3 tentativas)
- Mapeamento automático símbolo → coingecko_id
- Cache de coin list (1 hora TTL)
- Suporte multi-moeda (eur, usd, etc)

### 6. Interface Streamlit

**Localização**: `app.py`, `pages/`

**Routing**:
```python
# app.py - Entry point
if not logged_in:
    show_login_page()
elif page == "Portfolio":
    show_portfolio_page()
elif page == "Análise":
    show_portfolio_analysis()
# ...
```

**State Management**:
```python
# Sessão global
st.session_state['user_id']
st.session_state['username']
st.session_state['is_admin']

# Cache de preços temporários
st.session_state['_prices_session_cache']
```

**Componentes Interativos**:
- `st.selectbox()`: Seleção de utilizadores, ativos
- `st.date_input()`: Filtros de data
- `st.metric()`: KPIs com delta
- `st.dataframe()`: Tabelas interativas
- `st.plotly_chart()`: Gráficos Plotly

## Fluxos de Dados Principais

### Fluxo 1: Depósito → Alocação de Shares

```
1. Admin acede a páginas/users.py
2. Seleciona utilizador e insere valor de depósito
3. Sistema insere em t_user_capital_movements (credit)
4. services/shares.py:
   a. Calcula NAV total do fundo ANTES do depósito
   b. Calcula NAV/share = (NAV atual - depósito) ÷ total shares
   c. Shares alocadas = depósito ÷ NAV/share
   d. Insere registo em t_user_shares
5. UI atualiza com mensagem de sucesso e shares alocadas
```

### Fluxo 2: Análise de Portfólio

```
1. User acede a pages/portfolio_analysis.py
2. Sistema determina contexto (utilizador individual ou fundo completo)
3. Carrega movimentos de capital e transações da BD
4. Identifica todas as datas de eventos (depósitos + transações + dia 1 mês)
5. Para cada data:
   a. services/snapshots.py busca preços históricos (DB-first)
   b. Calcula holdings na data × preços da data
   c. Calcula caixa disponível na data
   d. Saldo na data = caixa + holdings
6. Renderiza gráfico Plotly com 3 linhas
7. Calcula métricas de HOJE:
   a. services/coingecko.py busca preços atuais
   b. Valoriza holdings com preços de hoje
   c. Calcula NAV atual
8. Exibe composição do portfólio e Top Holders
```

### Fluxo 3: Transação de Compra

```
1. User acede a pages/portfolio.py
2. Seleciona "Comprar" e escolhe ativo
3. Opcionalmente clica "Usar preço de mercado":
   → services/coingecko.py busca preço atual
4. Insere quantidade e data
5. Se data no passado:
   → services/snapshots.py busca preço histórico
6. Sistema valida saldo de caixa disponível:
   a. Calcula caixa = depósitos - levantamentos - compras + vendas
   b. Se insuficiente, mostra erro
7. Insere em t_transactions (type='buy')
8. Holdings do fundo atualizados automaticamente
```

## Performance e Otimizações

### 1. Prefetch de Preços Históricos

**Problema**: Buscar preço por preço = muitas chamadas API = rate limit

**Solução**:
```python
# Identificar todas as datas necessárias
all_dates = set(movement_dates + transaction_dates + monthly_markers)

# Buscar todos os preços de uma vez (com progress bar)
prices_cache = {}
for date in all_dates:
    prices_cache[date] = get_historical_prices_by_symbol(symbols, date)
```

### 2. Session Cache

```python
# Em services/snapshots.py
_prices_session_cache = {}

def get_historical_prices_by_symbol(symbols, date):
    cache_key = f"{'-'.join(sorted(symbols))}_{date}"
    if cache_key in _prices_session_cache:
        return _prices_session_cache[cache_key]
    
    # ... buscar preços ...
    _prices_session_cache[cache_key] = result
    return result
```

### 3. Bulk Database Queries

```python
# ❌ LENTO: N queries
for asset in assets:
    price = execute_query("SELECT price FROM t_price_snapshots WHERE asset_id = %s", (asset,))

# ✅ RÁPIDO: 1 query
prices = execute_query("""
    SELECT asset_id, price 
    FROM t_price_snapshots 
    WHERE asset_id = ANY(%s)
""", (asset_ids,))
```

### 4. Índices na Base de Dados

```sql
-- Lookup rápido de preços
CREATE INDEX idx_price_snapshots_lookup 
ON t_price_snapshots(asset_id, snapshot_date, vs_currency);

-- Queries por utilizador
CREATE INDEX idx_user_shares_user 
ON t_user_shares(user_id);

CREATE INDEX idx_capital_movements_user 
ON t_user_capital_movements(user_id);
```

## Segurança

### Autenticação
- ✅ Bcrypt hash com salt
- ✅ Sessão server-side
- ✅ Proteção de rotas com decorator
- ✅ Validação de is_admin

### SQL Injection
- ✅ Queries parametrizadas
- ✅ Uso de psycopg2 placeholders (%s)
- ✅ Nunca string concatenation em SQL

### Validações
- ✅ Saldo de caixa antes de compras
- ✅ Shares suficientes antes de levantamentos
- ✅ Tipos de dados corretos (Decimal para valores monetários)
- ✅ Datas válidas

### Rate Limiting
- ✅ Delay de 2 segundos entre chamadas CoinGecko
- ✅ Retry com exponential backoff
- ✅ Cache agressivo para reduzir chamadas API

## Deployment

### Requisitos
- Python 3.10+
- PostgreSQL 12+
- 512MB RAM mínimo
- Conexão internet (para CoinGecko API)

### Variáveis de Ambiente
```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
COINGECKO_API_KEY=optional  # Para tier pago
SECRET_KEY=random_string_for_sessions
```

### Comandos
```bash
# Instalar dependências
pip install -r requirements.txt

# Inicializar BD
psql -U user -d dbname -f database/tables.sql

# Executar migrações
python database/migrations/run_migration_007.py

# Lançar aplicação
streamlit run app.py --server.port 8501
```

## Manutenção

### Backups
```bash
# Backup completo
pg_dump -U user dbname > backup_$(date +%Y%m%d).sql

# Backup apenas dados de shares (crítico)
pg_dump -U user -t t_user_shares dbname > shares_backup.sql
```

### Monitorização
- Tamanho de `t_price_snapshots` (pode crescer muito)
- Tempo de resposta de CoinGecko API
- Erros de conexão BD no log
- Rate limits (429 errors)

### Limpeza de Cache
```sql
-- Apagar snapshots antigos (> 2 anos)
DELETE FROM t_price_snapshots 
WHERE snapshot_date < NOW() - INTERVAL '2 years';
```

---

**Próximo**: [Sistema de Shares/NAV →](02-shares-nav.md)
