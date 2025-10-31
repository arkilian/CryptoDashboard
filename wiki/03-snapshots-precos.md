# 📸 Sistema de Snapshots e Preços

## Visão Geral

O sistema de snapshots é uma **camada de cache inteligente** que armazena preços históricos de criptomoedas na base de dados local, reduzindo drasticamente as chamadas à API do CoinGecko e melhorando performance.

### Por que Snapshots?

**Problema sem cache:**
```
Análise de portfólio com 100 datas × 5 ativos = 500 chamadas API
CoinGecko rate limit: ~30 chamadas/minuto
Tempo necessário: ~17 minutos 😱
Erro 429 (Too Many Requests): frequente ⚠️
```

**Solução com snapshots:**
```
1ª execução: 500 chamadas (salva tudo na BD)
2ª execução: 0 chamadas (lê tudo da BD) ⚡
Tempo: < 1 segundo 🚀
```

## Arquitetura

### Camadas de Cache

```
┌─────────────────────────────────────────┐
│  1. Session Cache (Memória)            │
│  Dicionário Python temporário           │
│  Duração: 1 sessão Streamlit            │
└─────────────────────────────────────────┘
               ↓ (se não encontrar)
┌─────────────────────────────────────────┐
│  2. Database Cache (PostgreSQL)         │
│  Tabela t_price_snapshots               │
│  Duração: Permanente                    │
└─────────────────────────────────────────┘
               ↓ (se não encontrar)
┌─────────────────────────────────────────┐
│  3. CoinGecko API (Externa)             │
│  Endpoints: /simple/price, /history     │
│  Rate limit: ~30/min grátis             │
└─────────────────────────────────────────┘
```

### Fluxo de Dados

```python
Pedido: Preço de ADA em 2025-01-15

1. Verificar Session Cache
   └─> _prices_session_cache[(ADA, 2025-01-15)]
       └─> Se encontrar: RETURN ⚡
       
2. Verificar Database
   └─> SELECT price FROM t_price_snapshots 
       WHERE asset_id=X AND snapshot_date='2025-01-15'
       └─> Se encontrar: 
           - Guarda em Session Cache
           - RETURN ⚡
       
3. Chamar CoinGecko API
   └─> GET /coins/cardano/history?date=15-01-2025
       └─> Parse response
           - Guarda em Database
           - Guarda em Session Cache
           - time.sleep(2)  # Rate limiting
           - RETURN
```

## Tabela t_price_snapshots

### Schema

```sql
CREATE TABLE t_price_snapshots (
    snapshot_id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL REFERENCES t_assets(asset_id),
    snapshot_date DATE NOT NULL,
    price NUMERIC(20, 8) NOT NULL,
    vs_currency VARCHAR(10) NOT NULL DEFAULT 'eur',
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraint: 1 preço por ativo/data/moeda
    UNIQUE(asset_id, snapshot_date, vs_currency)
);

-- Índice para lookup rápido
CREATE INDEX idx_price_snapshots_lookup 
ON t_price_snapshots(asset_id, snapshot_date, vs_currency);
```

### Características

- ✅ **Único**: Não permite duplicatas (UNIQUE constraint)
- ✅ **Indexado**: Queries extremamente rápidas
- ✅ **Preciso**: NUMERIC(20,8) para 8 casas decimais
- ✅ **Multi-moeda**: Suporta EUR, USD, etc
- ✅ **Auditável**: Timestamp de quando foi criado

### Exemplo de Dados

```
snapshot_id | asset_id | snapshot_date | price      | vs_currency | created_at
------------|----------|---------------|------------|-------------|--------------------
1           | 3        | 2025-01-01    | 0.52000000 | eur         | 2025-10-31 10:30:00
2           | 3        | 2025-01-15    | 0.48500000 | eur         | 2025-10-31 10:30:15
3           | 3        | 2025-02-01    | 0.51200000 | eur         | 2025-10-31 10:30:30
4           | 1        | 2025-01-01    | 40500.50   | eur         | 2025-10-31 10:31:00
```

## Integração CoinGecko

### Cliente CoinGecko (`services/coingecko.py`)

#### 1. Mapeamento Símbolo → ID

**Problema**: CoinGecko usa IDs internos, não símbolos

```
Símbolo → ID
ADA     → cardano
BTC     → bitcoin
ETH     → ethereum
```

**Solução**: Cache de mapeamento

```python
# Mapeamento rápido para moedas comuns
COMMON_SYMBOL_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "ADA": "cardano",
    "SOL": "solana",
    # ...
}

def _symbol_to_id(symbol: str) -> Optional[str]:
    sym = symbol.upper()
    
    # 1. Verificar cache local
    if sym in _symbol_to_id_cache:
        return _symbol_to_id_cache[sym]
    
    # 2. Consultar lista completa do CoinGecko (cache 1h)
    coins = _get_coin_list()  # GET /coins/list
    
    # 3. Buscar por symbol (case-insensitive)
    for coin in coins:
        if coin.get("symbol", "").upper() == sym:
            coin_id = coin.get("id")
            _symbol_to_id_cache[sym] = coin_id
            return coin_id
    
    return None
```

#### 2. Preços Atuais

**Endpoint**: `GET /simple/price`

**Parâmetros**:
```
ids: bitcoin,ethereum,cardano
vs_currencies: eur
```

**Response**:
```json
{
  "bitcoin": {"eur": 50000.00},
  "ethereum": {"eur": 3000.00},
  "cardano": {"eur": 0.52}
}
```

**Implementação**:
```python
def get_price_by_symbol(
    symbols: List[str], 
    vs_currency: str = "eur"
) -> Dict[str, Optional[float]]:
    if not symbols:
        return {}
    
    # Mapear símbolos para IDs
    ids = []
    symbol_id_map = {}
    for sym in symbols:
        coin_id = _symbol_to_id(sym)
        if coin_id:
            symbol_id_map[sym] = coin_id
            ids.append(coin_id)
    
    if not ids:
        return {s: None for s in symbols}
    
    # Chamar API
    params = {
        "ids": ",".join(ids),
        "vs_currencies": vs_currency
    }
    
    # Retry com backoff
    retries = 3
    backoff = 1.0
    for attempt in range(retries):
        try:
            resp = requests.get(
                f"{BASE_URL}/simple/price",
                params=params,
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            
            # Mapear de volta para símbolos
            prices = {}
            for sym, coin_id in symbol_id_map.items():
                if coin_id in data and vs_currency in data[coin_id]:
                    prices[sym] = float(data[coin_id][vs_currency])
                else:
                    prices[sym] = None
            
            return prices
            
        except requests.RequestException as e:
            logger.warning(f"Tentativa {attempt + 1}: {e}")
            if attempt < retries - 1:
                time.sleep(backoff)
                backoff *= 2
            else:
                return {s: None for s in symbols}
```

#### 3. Preços Históricos

**Endpoint**: `GET /coins/{id}/history`

**Parâmetros**:
```
date: 31-10-2025  # Formato DD-MM-YYYY
```

**Response**:
```json
{
  "id": "cardano",
  "symbol": "ada",
  "market_data": {
    "current_price": {
      "eur": 0.524273
    }
  }
}
```

**Importante**: Este endpoint retorna o preço **do final do dia** (UTC).

**Uso**:
```python
# NÃO usado diretamente
# Chamado via services/snapshots.py
```

### Rate Limiting e Retry

**Estratégia**:
```python
retries = 3
backoff = 1.0  # segundos

for attempt in range(retries):
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
        
    except requests.RequestException as e:
        if attempt < retries - 1:
            time.sleep(backoff)
            backoff *= 2  # 1s → 2s → 4s
        else:
            logger.error(f"Falhou após {retries} tentativas: {e}")
            return None
```

**Rate Limiting Adicional**:
```python
# Em services/snapshots.py
# Após cada chamada bem-sucedida:
time.sleep(2)  # Aguarda 2 segundos
```

## Serviço de Snapshots (`services/snapshots.py`)

### Função Principal: `get_historical_price`

**Assinatura**:
```python
def get_historical_price(
    asset_id: int, 
    target_date: date
) -> Optional[float]
```

**Lógica**:
```python
def get_historical_price(asset_id: int, target_date: date) -> Optional[float]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # 1. Buscar na BD
        query = """
            SELECT price 
            FROM t_price_snapshots 
            WHERE asset_id = %s 
              AND snapshot_date = %s 
              AND vs_currency = 'eur'
        """
        cur.execute(query, (asset_id, target_date))
        result = cur.fetchone()
        
        if result:
            logger.info(f"✓ Preço em cache: asset_id={asset_id}, date={target_date}")
            return float(result[0])
        
        # 2. Não encontrado → Buscar na API
        logger.info(f"✗ Cache miss: asset_id={asset_id}, date={target_date} → API")
        
        # Obter coingecko_id do ativo
        cur.execute("SELECT coingecko_id FROM t_assets WHERE asset_id = %s", (asset_id,))
        asset_row = cur.fetchone()
        if not asset_row or not asset_row[0]:
            logger.warning(f"Ativo {asset_id} sem coingecko_id")
            return None
        
        coingecko_id = asset_row[0]
        
        # Determinar endpoint baseado na data
        today = date.today()
        
        if target_date >= today:
            # Preço atual
            url = f"{COINGECKO_BASE_URL}/simple/price"
            params = {"ids": coingecko_id, "vs_currencies": "eur"}
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            price = data.get(coingecko_id, {}).get("eur")
            
        else:
            # Preço histórico
            date_str = target_date.strftime("%d-%m-%Y")
            url = f"{COINGECKO_BASE_URL}/coins/{coingecko_id}/history"
            params = {"date": date_str}
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            price = data.get("market_data", {}).get("current_price", {}).get("eur")
        
        if not price:
            logger.warning(f"API não retornou preço para {coingecko_id} em {target_date}")
            return None
        
        # 3. Guardar na BD
        insert_query = """
            INSERT INTO t_price_snapshots (asset_id, snapshot_date, price, vs_currency)
            VALUES (%s, %s, %s, 'eur')
            ON CONFLICT (asset_id, snapshot_date, vs_currency) DO NOTHING
        """
        cur.execute(insert_query, (asset_id, target_date, float(price)))
        conn.commit()
        
        logger.info(f"✓ Preço guardado em cache: {float(price)} EUR")
        
        # 4. Rate limiting
        time.sleep(2)
        
        return float(price)
        
    except Exception as e:
        logger.error(f"Erro ao obter preço: {e}")
        conn.rollback()
        return None
    finally:
        cur.close()
        return_connection(conn)
```

### Bulk Fetching: `get_historical_prices_bulk`

**Problema**: Buscar 1 a 1 é lento mesmo com cache

**Solução**: Batch query na BD

```python
def get_historical_prices_bulk(
    asset_ids: List[int], 
    target_date: date
) -> Dict[int, Optional[float]]:
    if not asset_ids:
        return {}
    
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # 1. Buscar TODOS de uma vez na BD
        query = """
            SELECT asset_id, price 
            FROM t_price_snapshots 
            WHERE asset_id = ANY(%s) 
              AND snapshot_date = %s 
              AND vs_currency = 'eur'
        """
        cur.execute(query, (asset_ids, target_date))
        results = cur.fetchall()
        
        # Mapear resultados
        prices = {row[0]: float(row[1]) for row in results}
        found_ids = set(prices.keys())
        missing_ids = set(asset_ids) - found_ids
        
        logger.info(f"Bulk: {len(found_ids)} em cache, {len(missing_ids)} missing")
        
        # 2. Buscar individualmente os que faltam
        for asset_id in missing_ids:
            price = get_historical_price(asset_id, target_date)
            prices[asset_id] = price
        
        return prices
        
    finally:
        cur.close()
        return_connection(conn)
```

### By Symbol: `get_historical_prices_by_symbol`

**Problema**: UI trabalha com símbolos (ADA), BD com IDs (3)

**Solução**: Camada de tradução + session cache

```python
# Cache de sessão (memória)
_prices_session_cache = {}

def get_historical_prices_by_symbol(
    symbols: List[str], 
    target_date: date
) -> Dict[str, Optional[float]]:
    if not symbols:
        return {}
    
    # 1. Verificar session cache
    cache_key = f"{'-'.join(sorted(symbols))}_{target_date}"
    if cache_key in _prices_session_cache:
        logger.info(f"Session cache HIT: {cache_key}")
        return _prices_session_cache[cache_key]
    
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # 2. Mapear símbolos → asset_ids
        placeholders = ','.join(['%s'] * len(symbols))
        query = f"""
            SELECT asset_id, symbol 
            FROM t_assets 
            WHERE symbol IN ({placeholders})
        """
        cur.execute(query, symbols)
        rows = cur.fetchall()
        
        symbol_to_id = {row[1]: row[0] for row in rows}
        asset_ids = [symbol_to_id[sym] for sym in symbols if sym in symbol_to_id]
        
        # 3. Bulk fetch por IDs
        prices_by_id = get_historical_prices_bulk(asset_ids, target_date)
        
        # 4. Mapear de volta para símbolos
        prices_by_symbol = {}
        for sym in symbols:
            if sym in symbol_to_id:
                asset_id = symbol_to_id[sym]
                prices_by_symbol[sym] = prices_by_id.get(asset_id)
            else:
                prices_by_symbol[sym] = None
        
        # 5. Guardar em session cache
        _prices_session_cache[cache_key] = prices_by_symbol
        
        return prices_by_symbol
        
    finally:
        cur.close()
        return_connection(conn)
```

## Uso em Páginas

### Portfolio Analysis: Prefetch Pattern

**Problema**: 100 datas × 5 ativos = muitas queries

**Solução**: Prefetch tudo logo no início

```python
# pages/portfolio_analysis.py

# 1. Identificar TODAS as datas necessárias
event_dates = set(df_cap["date"].tolist())  # Depósitos/levantamentos
if not df_all_tx.empty:
    event_dates.update(df_all_tx["date"].tolist())  # Transações

# Adicionar dia 1 de cada mês
from dateutil.relativedelta import relativedelta
current_month = start_date.replace(day=1)
while current_month <= end_date:
    if current_month >= start_date:
        event_dates.add(current_month)
    current_month = current_month + relativedelta(months=1)

all_dates = sorted(event_dates)

# 2. Prefetch TODOS os preços
unique_symbols = df_all_tx['symbol'].unique().tolist()
prices_cache = {}

if unique_symbols:
    total_dates = len(all_dates)
    progress_text = st.empty()
    progress_bar = st.progress(0.0)
    
    for idx, calc_date in enumerate(all_dates):
        progress_text.text(f"🔄 A carregar preços... {idx+1}/{total_dates}")
        progress_bar.progress((idx + 1) / total_dates)
        
        # Busca bulk (BD-first, API on miss)
        prices = get_historical_prices_by_symbol(unique_symbols, calc_date)
        prices_cache[calc_date] = prices
    
    progress_text.empty()
    progress_bar.empty()

# 3. Usar cache local (sem mais chamadas à BD/API)
for calc_date in all_dates:
    historical_prices = prices_cache.get(calc_date, {})
    
    for sym, qty in holdings.items():
        if qty > 0:
            price = historical_prices.get(sym)
            if price:
                holdings_value += qty * float(price)
```

**Benefícios**:
- ✅ Uma única passagem pela lista de datas
- ✅ Progress bar para o utilizador
- ✅ Session cache evita duplicatas
- ✅ Bulk queries minimizam overhead da BD
- ✅ Rate limiting aplicado automaticamente

### Transações: On-Demand Fetch

**Contexto**: Utilizador seleciona data no passado

```python
# pages/portfolio.py (ou similar)

selected_date = st.date_input("Data da transação", value=date.today())

if st.button("Usar preço de mercado"):
    if selected_date >= date.today():
        # Preço atual
        prices = get_price_by_symbol([selected_asset], vs_currency='eur')
        price = prices.get(selected_asset)
    else:
        # Preço histórico (via snapshot)
        asset_id = get_asset_id_by_symbol(selected_asset)
        price = get_historical_price(asset_id, selected_date)
    
    if price:
        st.session_state['transaction_price'] = price
        st.success(f"Preço carregado: €{price:.6f}")
```

## Performance

### Benchmarks

**Cenário**: Portfolio com 50 datas, 3 ativos

| Método | Tempo | Chamadas API |
|--------|-------|--------------|
| Sem cache | ~300s | 150 |
| Cache BD apenas | ~5s | 0 (após 1ª vez) |
| Cache BD + Session | ~0.8s | 0 (após 1ª vez) |
| Prefetch + Bulk | ~0.5s | 0 (após 1ª vez) |

### Estatísticas de Cache

```python
# Query útil para monitorização
def get_cache_stats():
    query = """
        SELECT 
            COUNT(*) AS total_snapshots,
            COUNT(DISTINCT asset_id) AS total_assets,
            MIN(snapshot_date) AS oldest_date,
            MAX(snapshot_date) AS newest_date,
            pg_size_pretty(pg_total_relation_size('t_price_snapshots')) AS table_size
        FROM t_price_snapshots;
    """
    return execute_query(query)[0]
```

**Output Exemplo**:
```python
{
    'total_snapshots': 1547,
    'total_assets': 12,
    'oldest_date': date(2024, 1, 1),
    'newest_date': date(2025, 10, 31),
    'table_size': '128 kB'
}
```

## Gestão de Cache

### Limpeza de Dados Antigos

```sql
-- Apagar snapshots com mais de 2 anos
DELETE FROM t_price_snapshots 
WHERE snapshot_date < NOW() - INTERVAL '2 years';

-- Ou por número de registos
DELETE FROM t_price_snapshots 
WHERE snapshot_id IN (
    SELECT snapshot_id 
    FROM t_price_snapshots 
    ORDER BY snapshot_date ASC 
    LIMIT 10000
);
```

### Rebuild de Cache

**Se API mudou ou há inconsistências**:

```sql
-- 1. Backup
CREATE TABLE t_price_snapshots_backup AS 
SELECT * FROM t_price_snapshots;

-- 2. Limpar
TRUNCATE TABLE t_price_snapshots;

-- 3. Recarregar
-- Sistema automaticamente refetch na próxima análise
```

### UI de Administração

Em `pages/settings.py`:

```python
st.subheader("📸 Gestão de Snapshots")

stats = get_cache_stats()
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Snapshots", stats['total_snapshots'])
with col2:
    st.metric("Ativos Cacheados", stats['total_assets'])
with col3:
    st.metric("Tamanho", stats['table_size'])

if st.button("🗑️ Limpar Cache Antigo (>2 anos)"):
    deleted = cleanup_old_snapshots(days=730)
    st.success(f"✓ {deleted} registos apagados")

if st.button("🔄 Rebuild Cache Completo"):
    if st.checkbox("Confirmar (vai apagar tudo)"):
        truncate_snapshots()
        st.warning("Cache limpo. Será reconstruído na próxima análise.")
```

## Troubleshooting

### Erro 429 (Too Many Requests)

**Sintomas**: Múltiplos erros de rate limit

**Causas**:
- Sleep de 2 segundos removido
- Prefetch não implementado (muitas chamadas sequenciais)
- Cache não funcional (sempre vai à API)

**Soluções**:
```python
# 1. Verificar sleep está ativo
time.sleep(2)  # Em get_historical_price após API call

# 2. Usar prefetch pattern
# (ver exemplo em Portfolio Analysis acima)

# 3. Verificar unique constraint na BD
# Se falhar, duplicatas causam reprocessing
```

### Preços NULL

**Sintomas**: Alguns ativos sem preço

**Causas**:
- `coingecko_id` errado ou NULL em t_assets
- Ativo não existe no CoinGecko
- Data muito antiga (CoinGecko só tem desde certa data)

**Soluções**:
```sql
-- Verificar coingecko_id
SELECT asset_id, symbol, coingecko_id 
FROM t_assets 
WHERE coingecko_id IS NULL OR coingecko_id = '';

-- Atualizar manualmente
UPDATE t_assets 
SET coingecko_id = 'cardano' 
WHERE symbol = 'ADA';

-- Verificar disponibilidade no CoinGecko
-- Usar: https://www.coingecko.com/en/coins/[id]
```

### Session Cache Não Limpa

**Sintomas**: Valores antigos mesmo após refresh

**Causa**: Cache em `st.session_state` persiste

**Solução**:
```python
# Botão de reset
if st.button("🔄 Limpar Cache de Sessão"):
    if '_prices_session_cache' in st.session_state:
        del st.session_state['_prices_session_cache']
    st.success("Cache limpo!")
    st.rerun()
```

## Boas Práticas

### ✅ DO

- Usar prefetch para múltiplas datas
- Implementar bulk queries quando possível
- Respeitar rate limits (sleep 2s)
- Logar cache hits/misses para monitorização
- Validar `coingecko_id` antes de chamar API
- Usar session cache para evitar duplicatas

### ❌ DON'T

- ❌ Chamar API em loop sem sleep
- ❌ Fazer queries 1-a-1 quando bulk é possível
- ❌ Assumir que preço sempre existe
- ❌ Ignorar erros de API (retry é crítico)
- ❌ Deixar cache crescer infinitamente sem limpeza

## Extensões Futuras

### Multi-Moeda

```python
def get_historical_price(
    asset_id: int, 
    target_date: date,
    vs_currency: str = 'eur'  # ← Adicionar parâmetro
) -> Optional[float]:
    # Queries adaptadas para incluir vs_currency
    # ...
```

### Cache de Coin List

```python
# Criar tabela t_coingecko_coins
CREATE TABLE t_coingecko_coins (
    coin_id VARCHAR(100) PRIMARY KEY,
    symbol VARCHAR(20),
    name VARCHAR(200),
    last_updated TIMESTAMP DEFAULT NOW()
);

# Popular periodicamente (cronjob ou button)
```

### Warm-up de Cache

```python
def warm_up_cache(
    asset_ids: List[int],
    start_date: date,
    end_date: date
):
    """Preenche cache para período específico"""
    dates = pd.date_range(start_date, end_date, freq='D')
    
    for date in dates:
        get_historical_prices_bulk(asset_ids, date.date())
        # Progress bar...
```

---

**Anterior**: [← Sistema de Shares/NAV](02-shares-nav.md)  
**Próximo**: [Modelo de Negócio →](04-modelo-negocio.md)
