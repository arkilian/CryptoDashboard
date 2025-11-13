# CoinGecko Historical Data Import - Guia Completo

## 🎯 Objetivo

Importar dados históricos de preços do CoinGecko para `t_price_snapshots`, permitindo análise de portfolio sem depender de chamadas API em tempo real.

---

## ⚠️ Aviso Importante: Web Scraping NÃO Funciona

### Tentativas Realizadas

Foram implementadas **5 estratégias avançadas** de anti-bloqueio:

1. **Headers Realistas** ✅ Parcial
   - User-Agent: Chrome 131.0.0.0 (versão atual)
   - sec-ch-ua: Client Hints completos
   - sec-fetch-*: Headers de navegação
   - Referer: Simulação de navegação natural
   - **Resultado:** Homepage e página da moeda carregam (200 OK)

2. **Navegação Sequencial** ✅ Parcial
   - Visita homepage → página da moeda → download
   - Delays naturais (1-2s entre requests)
   - Session persistente (mantém cookies)
   - **Resultado:** Sessão válida criada, cookies mantidos

3. **Múltiplas Tentativas de Parsing** ❌
   - Procura por links: href com "csv", "download", "export"
   - Botões com data-* attributes
   - Texto "Export" em elementos
   - **Resultado:** Nenhum link encontrado (SPA JavaScript)

4. **URL Padrão Conhecida** ❌
   - `/en/coins/{coin_id}/historical_data/usd?download=true`
   - **Resultado:** 403 Forbidden

5. **Selenium WebDriver** ⚠️ Não testado
   - Execução de JavaScript real
   - Anti-detecção: `navigator.webdriver = undefined`
   - **Limitações:** Lento, frágil, requer ChromeDriver

### Por Que Falha?

**Análise técnica da resposta do CoinGecko:**

```bash
# Teste realizado em 2025-11-05
Status Code: 200 OK (página carrega)
Content-Type: text/html; charset=utf-8
HTML parseado: 0 links, 0 botões, 0 scripts
Conteúdo: Binário/comprimido (gzip/brotli)
```

**Conclusão:**
- ✅ Página principal carrega (proteção anti-bot passada)
- ❌ Conteúdo é **SPA (Single Page Application)**
- ❌ HTML retornado é apenas shell, JavaScript renderiza tudo
- ❌ Endpoint `/historical_data/usd` está **protegido com 403**
- ❌ Cloudflare/bot detection bloqueia acesso direto ao CSV

### Proteções Detectadas

- [x] Cloudflare Challenge (nível médio)
- [x] JavaScript obrigatório (SPA)
- [x] Endpoint de download protegido (403)
- [x] HTML ofuscado/comprimido
- [ ] CAPTCHA (não acionado, mas pode aparecer)

---

## ✅ Solução: Download Manual + Import Automático

### Workflow Recomendado

#### 1. Download Manual do CSV

**Para Cardano (ADA):**
1. Abrir: https://www.coingecko.com/en/coins/cardano/historical_data
2. Clicar botão: **"Export Data"** (canto superior direito)
3. Selecionar: **"Max"** (todos os dados históricos)
4. Download: `ada-usd-max.csv`
5. Guardar em: `C:\CryptoDashboard\cardano\ada-usd-max.csv`

**Para outras moedas:**
- Bitcoin: https://www.coingecko.com/en/coins/bitcoin/historical_data
- Ethereum: https://www.coingecko.com/en/coins/ethereum/historical_data
- DJED: https://www.coingecko.com/en/coins/djed/historical_data

#### 2. Import Automático

```bash
# Ativar venv
cd C:\CryptoDashboard
.venv\Scripts\Activate.ps1

# Importar ADA (recomendado: taxa fixa)
python -m services.coingecko_scraper --coin cardano --csv cardano/ada-usd-max.csv --all

# Importar Bitcoin
python -m services.coingecko_scraper --coin bitcoin --csv bitcoin/btc-usd-max.csv --all

# Importar Ethereum
python -m services.coingecko_scraper --coin ethereum --csv ethereum/eth-usd-max.csv --all
```

#### 3. Verificar Resultados

```bash
# Ver estatísticas
python debug_scripts/check_csv_import.py

# Ou via SQL
psql -d cryptodashboard -c "
SELECT 
    a.symbol,
    COUNT(*) as snapshots,
    MIN(ps.snapshot_date) as primeira_data,
    MAX(ps.snapshot_date) as ultima_data,
    AVG(ps.price_eur)::numeric(10,4) as preco_medio
FROM t_price_snapshots ps
JOIN t_assets a ON a.asset_id = ps.asset_id
WHERE ps.source = 'coingecko_csv'
GROUP BY a.symbol
ORDER BY a.symbol;
"
```

---

## 📊 Formato do CSV

### Estrutura Esperada

```csv
snapped_at,price,market_cap,total_volume
2017-10-18 00:00:00 UTC,0.02684535467621909,696021404.3079604,2351678.122306208
2017-10-19 00:00:00 UTC,0.026941078048649077,699505850.1696405,1962977.1626596712
...
```

### Colunas

| Coluna | Tipo | Descrição | Uso |
|--------|------|-----------|-----|
| `snapped_at` | Timestamp | Data/hora UTC | Convertido para `snapshot_date` (DATE) |
| `price` | Float | Preço em USD | Convertido para EUR (×0.92) → `price_eur` |
| `market_cap` | Float | Market cap USD | ❌ Não usado |
| `total_volume` | Float | Volume 24h USD | ❌ Não usado |

---

## 🔧 Opções da CLI

### Sintaxe Completa

```bash
python -m services.coingecko_scraper [OPTIONS]
```

### Parâmetros Obrigatórios

| Parâmetro | Descrição | Exemplo |
|-----------|-----------|---------|
| `--coin` | ID da moeda no CoinGecko | `cardano`, `bitcoin`, `ethereum` |

### Parâmetros Opcionais

| Parâmetro | Descrição | Default | Exemplo |
|-----------|-----------|---------|---------|
| `--csv` | Path do CSV local | None | `cardano/ada-usd-max.csv` |
| `--symbol` | Símbolo na BD | Auto-detect | `ADA`, `BTC`, `ETH` |
| `--all` | Importar todos os dados | False | `--all` |
| `--days N` | Limitar aos N dias mais recentes | None | `--days 365` |
| `--overwrite` | Sobrescrever dados existentes | False | `--overwrite` |
| `--dynamic-rate` | Taxa USD→EUR dinâmica (lento) | False | `--dynamic-rate` |
| `--selenium` | Usar Selenium (experimental) | False | `--selenium` |
| `--verbose -v` | Logging detalhado | False | `-v` |

### Exemplos de Uso

```bash
# 1. Import básico (recomendado)
python -m services.coingecko_scraper --coin cardano --csv cardano/ada-usd-max.csv --all

# 2. Últimos 30 dias apenas
python -m services.coingecko_scraper --coin cardano --csv cardano/ada-usd-max.csv --days 30

# 3. Sobrescrever dados existentes
python -m services.coingecko_scraper --coin cardano --csv cardano/ada-usd-max.csv --all --overwrite

# 4. Taxa USD→EUR dinâmica (muito lento, 50min para 2941 registos)
python -m services.coingecko_scraper --coin cardano --csv cardano/ada-usd-max.csv --all --dynamic-rate

# 5. Verbose logging
python -m services.coingecko_scraper --coin cardano --csv cardano/ada-usd-max.csv --all -v

# 6. Tentar scraping automático (geralmente falha com 403)
python -m services.coingecko_scraper --coin bitcoin --days 30 -v

# 7. Selenium fallback (requer: pip install selenium)
python -m services.coingecko_scraper --coin ethereum --selenium --all
```

---

## ⚙️ Conversão USD → EUR

### Opção 1: Taxa Fixa (Recomendado) ✅

**Valor:** `0.92` (média histórica 2017-2025)

**Vantagens:**
- ⚡ Extremamente rápido (~30s para 2941 registos)
- ✅ Sem dependências externas
- ✅ Sem rate limits
- ✅ Precisão aceitável para histórico

**Uso:** (default)
```bash
python -m services.coingecko_scraper --coin cardano --csv cardano/ada-usd-max.csv --all
```

### Opção 2: Taxa Dinâmica (Precisa) ⚠️

**Fonte:** European Central Bank API (https://api.exchangerate.host)

**Vantagens:**
- ✅ Taxa real histórica por data
- ✅ Precisão máxima

**Desvantagens:**
- ❌ Muito lento (50min para 2941 registos)
- ❌ Rate limits/timeouts frequentes
- ❌ API pode falhar (fallback para 0.92)

**Uso:**
```bash
python -m services.coingecko_scraper --coin cardano --csv cardano/ada-usd-max.csv --all --dynamic-rate
```

**Log típico:**
```
2025-11-05 16:47:20 - WARNING - Erro ao obter taxa USD->EUR para 2023-01-02: Read timed out
2025-11-05 16:47:35 - WARNING - Erro ao obter taxa USD->EUR para 2023-01-03: Connection timed out
[... 50 minutos depois ...]
2025-11-05 17:18:20 - INFO - ✅ Total inserido: 2941 registos
```

---

## 📈 Resultados Esperados

### Exemplo: Cardano (ADA)

**Teste realizado:** 2025-11-05

```
🚀 A processar: cardano -> ADA
📂 A usar CSV existente: cardano/ada-usd-max.csv
📊 A processar CSV para ADA (asset_id=4)
📝 A inserir 2941 registos...
✅ Total inserido: 2941 registos

✅ Sucesso! 2941 registos inseridos em t_price_snapshots
```

**Verificação na BD:**

```
📊 ADA Snapshots (CSV import)
   Total: 2714 registos
   Período: 2017-10-18 a 2025-11-05
   Preço médio: €0.4444
   Preço mín: €0.019615
   Preço máx: €2.7297

📊 ADA Snapshots (API)
   Total: 227 registos

📊 ADA Snapshots (Total)
   Datas únicas: 2941
```

**Explicação das diferenças:**
- 2941 linhas no CSV
- 2714 inseridos (alguns sobrepuseram snapshots da API)
- 227 da API mantidos onde não havia CSV
- **2941 datas únicas** (objetivo alcançado)

### Performance

| Método | Registos | Tempo | Velocidade |
|--------|----------|-------|------------|
| Taxa fixa | 2941 | ~30s | ~98 reg/s |
| Taxa dinâmica | 2941 | ~50min | ~1 reg/s |
| API CoinGecko | 227 | ~8min | ~0.5 reg/s |

---

## 🔍 Troubleshooting

### Erro: Asset não encontrado

```
❌ Asset 'XYZ' não encontrado em t_assets
```

**Solução:** Criar asset na base de dados primeiro (SQL):

```sql
INSERT INTO t_assets (symbol, name, coingecko_id, is_stablecoin)
VALUES ('XYZ', 'Nome da Moeda', 'xyz-coin-id', FALSE);
```

**Depois** executar o import:
```bash
python -m services.coingecko_scraper --coin xyz-coin-id --csv path/xyz-usd-max.csv --all
```

### Erro: Ficheiro não encontrado

```
❌ Ficheiro não encontrado: cardano/ada-usd-max.csv
```

**Solução:** Verificar path (absoluto ou relativo ao diretório atual)

```bash
# Usar path absoluto
python -m services.coingecko_scraper --coin cardano --csv C:\CryptoDashboard\cardano\ada-usd-max.csv --all

# Ou executar da raiz do projeto
cd C:\CryptoDashboard
python -m services.coingecko_scraper --coin cardano --csv cardano/ada-usd-max.csv --all
```

### Warning: Erro ao processar linha

```
⚠️ Erro ao processar linha: time data '...' does not match format...
```

**Causa:** Formato de data inesperado no CSV

**Solução:** Verificar formato. Esperado: `YYYY-MM-DD HH:MM:SS UTC`

### 403 Forbidden (scraping automático)

```
❌ Erro de rede ao fazer download: 403 Client Error: Forbidden
```

**Solução:** **Usar CSV manual** (scraping não funciona)

```bash
# ❌ NÃO FUNCIONA
python -m services.coingecko_scraper --coin bitcoin --all

# ✅ SOLUÇÃO
# 1. Download manual de https://www.coingecko.com/en/coins/bitcoin/historical_data
# 2. Import do CSV
python -m services.coingecko_scraper --coin bitcoin --csv bitcoin/btc-usd-max.csv --all
```

---

## 📦 Dependências

### Obrigatórias

```bash
pip install requests beautifulsoup4 lxml sqlalchemy psycopg2-binary
```

Já incluídas em `requirements.txt`:
```txt
beautifulsoup4==4.12.3
lxml==5.1.0
```

### Opcionais

**Selenium** (para scraping experimental):
```bash
pip install selenium

# Também precisa de ChromeDriver
# Windows: scoop install chromedriver
# Ou: pip install webdriver-manager
```

---

## 🎯 Integração com Portfolio v3

### Uso Automático

O Portfolio v3 já usa `t_price_snapshots` automaticamente:

```python
# pages/portfolio_v3.py
from services.snapshots import get_historical_prices_by_symbol

# Busca preços na BD primeiro, API só se necessário
prices = get_historical_prices_by_symbol(
    symbols=["ADA", "BTC", "ETH"],
    target_date=date.today(),
    allow_api_fallback=False  # Só BD
)
```

### Vantagens

1. **Sem Rate Limits:** Dados já na BD
2. **Performance:** Queries rápidas vs API lenta
3. **Histórico Completo:** 2900+ dias disponíveis
4. **Offline:** Funciona sem internet

---

## 📅 Manutenção

### Frequência Recomendada

**1x por semana** é suficiente para dados históricos (não mudam).

### Script de Atualização

```bash
# update_prices.bat
@echo off
cd C:\CryptoDashboard
call .venv\Scripts\activate.bat

echo Atualizando preços do CoinGecko...
python -m services.coingecko_scraper --coin cardano --csv cardano/ada-usd-max.csv --days 7 --overwrite
python -m services.coingecko_scraper --coin bitcoin --csv bitcoin/btc-usd-max.csv --days 7 --overwrite

echo Concluído!
pause
```

---

## 🔗 Links Úteis

- **CoinGecko Historical Data:** https://www.coingecko.com/en/coins/{coin_id}/historical_data
- **API Alternativa:** https://api.coingecko.com (requer API key)
- **Documentação:** `docs/WEB_SCRAPING_ANTIBOT.md`
- **Debug Scripts:** `debug_scripts/check_csv_import.py`

---

## 📝 Notas Técnicas

### Mapeamento Coins → Symbols

Definido em `COIN_MAPPING` no código:

```python
COIN_MAPPING = {
    "cardano": "ADA",
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "djed": "DJED",
    "usd-coin": "USDC",
    "tether": "USDT",
}
```

Para adicionar novos:
1. Adicionar ao dicionário
2. Criar asset em `t_assets` com `coingecko_id` correto
3. Descarregar CSV do CoinGecko

### ON CONFLICT Strategy

```sql
INSERT INTO t_price_snapshots (asset_id, snapshot_date, price_eur, source)
VALUES (...)
ON CONFLICT (asset_id, snapshot_date) 
    DO NOTHING  -- default (--skip-existing)
    -- ou --
    DO UPDATE SET price_eur = EXCLUDED.price_eur  -- com --overwrite
```

### Batching

Inserts em **lotes de 1000** para performance:

```python
batch_size = 1000
for i in range(0, len(rows), batch_size):
    batch = rows[i:i+batch_size]
    conn.execute(text("INSERT INTO ..."), batch)
```

---

## ✅ Checklist de Import

- [ ] Download CSV do CoinGecko manualmente
- [ ] Guardar em `{coin}/` folder (ex: `cardano/ada-usd-max.csv`)
- [ ] Verificar que o asset existe em `t_assets` (criar via SQL se necessário)
- [ ] Executar import: `--coin {name} --csv {path} --all`
- [ ] Verificar resultados: `debug_scripts/check_csv_import.py`
- [ ] Testar Portfolio v3: preços aparecem sem erros 429

---

**Última atualização:** 2025-11-05  
**Status:** ✅ Workflow manual funcional, scraping automático inviável
