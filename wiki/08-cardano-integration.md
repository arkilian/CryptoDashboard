# 🔷 Integração Blockchain Cardano

**Explorador completo da blockchain Cardano integrado ao Crypto Dashboard**

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Funcionalidades](#funcionalidades)
4. [Configuração](#configuração)
5. [API CardanoScan](#api-cardanoscan)
6. [Gestão de Wallets](#gestão-de-wallets)
7. [Gestão de Bancos](#gestão-de-bancos)
8. [Performance e Otimizações](#performance-e-otimizações)
9. [Casos de Uso](#casos-de-uso)
10. [Troubleshooting](#troubleshooting)

---

## Visão Geral

### O Que É?

A integração Cardano permite consultar informações em tempo real da blockchain Cardano diretamente no dashboard, sem necessidade de usar explorers externos para operações comuns.

### Principais Recursos

- ✅ **Consulta de Saldo**: Balance de ADA e tokens nativos
- ✅ **Staking Info**: Delegação, pool, recompensas
- ✅ **Histórico de Transações**: Completo com análise automática
- ✅ **Metadados Automáticos**: Nomes e decimais de tokens
- ✅ **Multi-Wallet**: Suporte a múltiplas wallets por utilizador
- ✅ **Configuração DB**: APIs e wallets geridas via interface

### Por Que Integrar?

**Antes**:
- Abrir CardanoScan em browser
- Copiar/colar endereços manualmente
- Consultar múltiplas páginas
- Sem histórico ou cache

**Agora**:
- Tudo no dashboard
- Wallets salvas e acessíveis
- Cache de metadados
- Análise automática de transações
- Ordenação inteligente (recentes primeiro)

---

## Arquitetura

### Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Streamlit)                     │
│  pages/cardano.py - Interface do explorador                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Service Layer (Business Logic)               │
│  services/cardano_api.py - Cliente CardanoScan API          │
│  └─ Cache de metadados (in-memory)                          │
│  └─ Análise de transações                                   │
│  └─ Resolução de nomes/decimais                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼─────────┐       ┌─────────▼──────────┐
│  Database Layer │       │  External API      │
│  ├─ t_wallet    │       │  CardanoScan v1    │
│  ├─ t_banco     │       │  api.cardanoscan.io│
│  └─ t_api_cardano│       └────────────────────┘
└─────────────────┘
```

### Fluxo de Dados

**1. Consulta de Balance:**
```
User → Select Wallet → API GET /address/summary → Parse → Display
                    ├─ Resolve token names (cache)
                    └─ Apply decimals
```

**2. Consulta de Staking:**
```
User → Input Address → API GET /account/info → Check delegation → Display
                                             ├─ Pool info
                                             └─ Rewards breakdown
```

**3. Consulta de Transações:**
```
User → Select Pages → API GET /transaction/list (reverse order)
                   ├─ Fetch from last page first
                   ├─ Sort by timestamp (DESC)
                   ├─ Analyze each TX (sent/received/contract)
                   ├─ Resolve token metadata (batch)
                   └─ Group by date → Display
```

---

## Funcionalidades

### 1️⃣ Saldo e Tokens

#### Informações Exibidas

- **💰 Balance ADA**: Saldo total em Lovelace convertido para ADA
- **📊 Total de Transações**: Contador de TXs confirmadas
- **🪙 Tokens Nativos**: Lista completa de tokens no endereço

#### Resolução de Metadados

**Problema Original**: Tokens aparecem como hex (ex: "Token 6df63e2f...")

**Solução Implementada**:
1. **Metadata API Lookup** (prioritário)
   - Consulta endpoint `/asset/{policyId}{assetName}` do CardanoScan
   - Extrai `name`, `decimals` de metadados on-chain
   
2. **Fallback para Campos Diretos**
   - Usa `assetNameAscii` se disponível
   - Decodifica hex de `assetName` para ASCII
   
3. **Último Recurso**
   - Mostra `policyId` truncado se nada funcionar

**Cache de Metadados**:
- Cache positivo: metadados encontrados ficam em memória
- Cache negativo: tokens sem metadata evitam re-consultas (prefixo `_neg_`)
- Batch fetching: coleta tokens únicos antes de buscar metadados

#### Decimais de Tokens

Tokens nativos Cardano não têm decimals padrão. O sistema:
1. Consulta metadata para campo `decimals`
2. Usa dicionário `TOKEN_DECIMALS_BY_POLICY` para tokens conhecidos:
   ```python
   TOKEN_DECIMALS_BY_POLICY = {
       "6df63e2fdde8b2c3b3396265b0cc824aa4fb999396b1c154280f6b0c": 6  # qDJED
   }
   ```
3. Default: 0 decimals (quantidade inteira)

**Exemplo**:
```
Quantidade raw: 45263147388
Decimals: 6
Display: 45,263.147388 qDJED
```

### 2️⃣ Staking

#### Estados Possíveis

**1. Delegado a Pool**
```
✅ Delegado
Pool: POOL1 - Example Stake Pool
Taxa: 2.5% | Margem: 340 ADA
Recompensas Totais: 1,250.50 ADA
Disponíveis: 50.25 ADA
Levantadas: 1,200.25 ADA
Stake Controlado: 10,500 ADA
```

**2. Não Delegado (Mas Tem Conta)**
```
⚠️ Não Delegado
Conta de staking existe mas não está delegada a nenhum pool
```

**3. Sem Conta de Staking**
```
ℹ️ Sem Conta de Staking
Este endereço não possui conta de staking registada
```

#### Informações Detalhadas

- **Pool Delegado**: Nome, ticker, pool ID
- **Taxa do Pool**: Fee fixo + margem variável
- **Recompensas**:
  - Total acumulado desde início
  - Disponíveis para levantar
  - Já levantadas (withdrawn)
- **Stake Controlado**: ADA total sendo usado para staking

### 3️⃣ Transações

#### Carregamento Inteligente

**Problema**: API retorna páginas da antiga para recente
- Página 1 = transações de 6 meses atrás
- Página 20 = transações de hoje

**Solução**: Busca reversa
```python
# Se total de páginas = 42 e max_pages = 5
# Buscar páginas: 42, 41, 40, 39, 38
start_page = max(1, page_count - max_pages + 1)
for page in range(page_count, start_page - 1, -1):
    fetch_page(page)
```

**Resultado**: Com 1 página já vê transações recentes!

#### Análise Automática

Cada transação é classificada como:

**Enviado (Sent) ↗**
- ADA saiu do endereço
- Cor vermelha
- Quantidade com sinal negativo

**Recebido (Received) ↙**
- ADA entrou no endereço
- Cor verde
- Quantidade com sinal positivo

**Contrato (Contract) ↔**
- Interação com smart contract
- DEX swap, stake, etc
- Cor azul/neutra

#### Ordenação

1. **Por Dia**: Dias mais recentes primeiro
2. **Dentro do Dia**: Transações ordenadas por timestamp DESC

```python
# Group by date
grouped = defaultdict(list)
for tx in transactions[:50]:
    date_key = timestamp.strftime("%b %d, %Y")
    grouped[date_key].append(tx)

# Sort days (newest first)
for date_str in sorted(grouped.keys(), reverse=True):
    # Sort TXs within day (newest first)
    txs_sorted = sorted(txs, key=lambda tx: tx['timestamp'], reverse=True)
```

#### Detalhes de Transação

- Hash completo com link para CardanoScan
- Tipo e descrição
- Quantidade ADA (líquida)
- Fees pagos
- Tokens movimentados (até 4 + contador)
- Data e hora

---

## Configuração

### Tabelas de Base de Dados

#### `t_api_cardano`

```sql
CREATE TABLE t_api_cardano (
    api_id SERIAL PRIMARY KEY,
    api_name VARCHAR(100) NOT NULL UNIQUE,
    api_key TEXT NOT NULL,
    base_url TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    default_address TEXT,
    rate_limit INTEGER,
    timeout INTEGER DEFAULT 10,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Campos**:
- `api_name`: Identificador único (ex: "CardanoScan Production")
- `api_key`: Chave de API (armazenada como texto)
- `base_url`: URL base da API (ex: https://api.cardanoscan.io/api/v1)
- `is_active`: Permite desativar sem remover
- `default_address`: Endereço padrão para auto-preencher
- `rate_limit`: Requests por minuto (informativo)
- `timeout`: Timeout em segundos (padrão: 10)

**View Helper**:
```sql
CREATE VIEW v_active_apis AS
SELECT * FROM t_api_cardano WHERE is_active = TRUE;
```

#### `t_wallet`

```sql
CREATE TABLE t_wallet (
    wallet_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES t_users(user_id),
    wallet_name VARCHAR(100) NOT NULL,
    wallet_type VARCHAR(20) NOT NULL,
    blockchain VARCHAR(50) NOT NULL,
    address TEXT NOT NULL,
    stake_address TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_primary BOOLEAN DEFAULT FALSE,
    balance_last_sync NUMERIC(20,8),
    last_sync_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Tipos de Wallet**:
- `hot`: Online, acesso frequente
- `cold`: Offline, armazenamento seguro
- `hardware`: Ledger, Trezor
- `exchange`: Wallet de exchange (Binance, etc)
- `defi`: Protocolos DeFi

**Blockchains Suportadas**:
- Cardano
- Ethereum
- Bitcoin
- Solana
- (Extensível para outras)

**Campos Cardano-Específicos**:
- `stake_address`: Endereço stake1... (para staking)
- `balance_last_sync`: Último saldo sincronizado
- `last_sync_at`: Timestamp da última sincronização

#### `t_banco`

```sql
CREATE TABLE t_banco (
    banco_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES t_users(user_id),
    bank_name VARCHAR(150) NOT NULL,
    account_holder VARCHAR(200) NOT NULL,
    iban VARCHAR(34),
    swift_bic VARCHAR(11),
    account_number VARCHAR(50),
    currency VARCHAR(3) DEFAULT 'EUR',
    country VARCHAR(100),
    branch VARCHAR(100),
    account_type VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    is_primary BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Tipos de Conta**:
- `checking`: Conta à ordem
- `savings`: Poupança
- `business`: Empresarial
- `investment`: Investimento

**Validação IBAN**:
```python
def validate_iban(iban: str) -> bool:
    """Validação básica de formato IBAN"""
    iban = iban.replace(' ', '').upper()
    return (
        len(iban) >= 15 and len(iban) <= 34 and
        iban[:2].isalpha() and
        iban[2:4].isdigit()
    )
```

### Página de Configurações

**Localização**: `pages/settings.py`

**Tabs Disponíveis**:
1. 💰 Taxas
2. 🪙 Ativos
3. 🏦 Exchanges
4. **🏦 Bancos** (Nova)
5. **🔌 APIs Cardano** (Nova)
6. **👛 Wallets** (Nova)
7. 📸 Snapshots
8. 🏷️ Tags

#### Tab: APIs Cardano

**Funcionalidades**:
- Listar todas as APIs cadastradas
- Adicionar nova API (nome, key, URL)
- Editar configurações existentes
- Ativar/Desativar API
- Remover API (com confirmação)
- Configurar rate limit e timeout

**Exemplo de Uso**:
```
Nome da API: CardanoScan Production
API Key: ••••••••••••••••
URL Base: https://api.cardanoscan.io/api/v1
Endereço Padrão: addr1q9y...xyz123
Rate Limit: 60 req/min
Timeout: 10 segundos
```

#### Tab: Wallets

**Funcionalidades**:
- Listar wallets do utilizador (ou todas se admin)
- Adicionar nova wallet
  - Nome, tipo, blockchain
  - Endereço principal
  - Stake address (Cardano)
- Editar wallet existente
- Definir wallet principal
- Remover wallet

**Filtros (Admin)**:
- Ver todas as wallets
- Filtrar por utilizador específico

#### Tab: Bancos

**Funcionalidades**:
- Listar contas bancárias
- Adicionar nova conta
  - Banco, titular, IBAN, SWIFT
  - Moeda, país, tipo de conta
- Editar conta existente
- Definir conta principal
- Remover conta
- Validação de IBAN

---

## API CardanoScan

### Endpoints Utilizados

#### 1. Address Summary
```
GET /address/summary?address={hex_address}
```

**Response**:
```json
{
  "balance": "5234567890",
  "totalTransactions": 42,
  "tokens": [
    {
      "policyId": "6df63e2f...",
      "assetName": "71444a4544",
      "assetNameAscii": "qDJED",
      "quantity": "45263147388"
    }
  ]
}
```

#### 2. Transaction List
```
GET /transaction/list?address={hex_address}&pageNo={page}
```

**Response**:
```json
{
  "count": 42,
  "transactions": [
    {
      "hash": "e37cad91...",
      "timestamp": 1697234567,
      "blockHeight": 8234567,
      "fees": "180000",
      "status": true,
      "inputs": [...],
      "outputs": [...]
    }
  ]
}
```

#### 3. Account Info (Staking)
```
GET /account/info?address={bech32_address}
```

**Response**:
```json
{
  "delegation": {
    "poolId": "pool1abc...",
    "active": true
  },
  "rewards": {
    "total": "125050000000",
    "available": "5025000000",
    "withdrawn": "120025000000"
  },
  "controlled_stake": "1050000000000"
}
```

#### 4. Asset Metadata
```
GET /asset/{policyId}{assetName}
```

**Response**:
```json
{
  "name": "qDJED",
  "decimals": 6,
  "ticker": "qDJED",
  "onchainMetadata": {
    "name": "qDJED",
    "decimals": 6
  }
}
```

### Rate Limits

**CardanoScan Free Tier**:
- 60 requests/minute
- ~1 request/second

**Estratégia de Mitigação**:
1. Cache de metadados (in-memory)
2. Batch fetching (coleta únicos antes de buscar)
3. Early returns (check campos simples antes de HTTP)
4. Negative cache (evita re-tentar tokens sem metadata)

### Conversões

#### Bech32 ↔ Hex

```python
import bech32

def bech32_to_hex(address: str) -> str:
    """addr1... → hex"""
    hrp, data = bech32.bech32_decode(address)
    return ''.join(f'{x:02x}' for x in bech32.convertbits(data, 5, 8, False))

def hex_to_bech32(hex_str: str, prefix='addr') -> str:
    """hex → addr1..."""
    data = bytes.fromhex(hex_str)
    converted = bech32.convertbits(data, 8, 5)
    return bech32.bech32_encode(prefix, converted)
```

#### Lovelace ↔ ADA

```python
def lovelace_to_ada(lovelace: int) -> float:
    """1 ADA = 1,000,000 Lovelace"""
    return lovelace / 1_000_000

def ada_to_lovelace(ada: float) -> int:
    return int(ada * 1_000_000)
```

---

## Gestão de Wallets

### CRUD Operations

**Módulo**: `database/wallets.py`

#### Criar Wallet
```python
from database.wallets import create_wallet

success, msg = create_wallet(
    user_id=1,
    wallet_name="Eternl Principal",
    wallet_type="hot",
    blockchain="Cardano",
    address="addr1q9y...",
    stake_address="stake1u8x...",
    is_primary=True
)
```

#### Listar Wallets
```python
from database.wallets import get_all_wallets, get_active_wallets

# Todas as wallets do utilizador
wallets = get_all_wallets(user_id=1)

# Apenas ativas
active = get_active_wallets(user_id=1)
```

#### Definir Primary
```python
from database.wallets import set_primary_wallet

success, msg = set_primary_wallet(wallet_id=5)
# Desativa is_primary de todas as outras wallets do mesmo user
```

#### Atualizar Saldo
```python
from database.wallets import update_balance_sync

update_balance_sync(
    wallet_id=5,
    balance=1250.5
)
# Atualiza balance_last_sync e last_sync_at
```

### Integração com Cardano Page

**Seleção de Wallet**:
```python
# Futuro: Dropdown para selecionar wallet
wallets = get_active_wallets(user_id)
selected = st.selectbox(
    "Wallet",
    options=[(w['wallet_name'], w['address']) for w in wallets]
)
address = selected[1]
```

---

## Gestão de Bancos

### CRUD Operations

**Módulo**: `database/banks.py`

#### Criar Conta Bancária
```python
from database.banks import create_bank

success, msg = create_bank(
    user_id=1,
    bank_name="Banco BPI",
    account_holder="João Silva",
    iban="PT50001234567890123456789",
    swift_bic="BBPIPTPL",
    currency="EUR",
    country="Portugal",
    account_type="checking",
    is_primary=True
)
```

#### Validar IBAN
```python
from database.banks import validate_iban

is_valid = validate_iban("PT50001234567890123456789")
# True se formato básico correto
```

#### Listar Bancos
```python
from database.banks import get_all_banks

banks = get_all_banks(user_id=1)
# Retorna lista com banco_id, bank_name, iban, etc
```

### Separação: Banco vs Exchange

**Conceito**:
- **Exchanges** (`t_exchanges`): Plataformas de trading (Binance, Kraken)
- **Bancos** (`t_banco`): Instituições bancárias tradicionais

**Por Que Separar?**
- Bancos têm IBAN/SWIFT
- Exchanges não têm dados bancários
- Tipos de conta diferentes
- Regulamentação diferente

**Uso em Transações**:
```python
# Depósito via banco
transaction_type = "deposit"
from_account_id = banco_id  # t_banco
to_account_id = None

# Compra via exchange
transaction_type = "buy"
from_account_id = exchange_id  # t_exchanges
```

---

## Performance e Otimizações

### 1. Cache de Metadados

**Problema**: Cada token faz 1 HTTP request

**Solução**: Cache em memória
```python
_asset_meta_cache = {}  # {key: metadata}

def get_asset_metadata(policy_id, asset_name):
    key = f"{policy_id}:{asset_name}"
    
    # Check cache
    if key in _asset_meta_cache:
        return _asset_meta_cache[key]
    
    # Fetch from API
    meta = fetch_metadata(policy_id, asset_name)
    
    # Store in cache
    _asset_meta_cache[key] = meta
    return meta
```

**Tipos de Cache**:
- **Positivo**: `{key: {name: "qDJED", decimals: 6}}`
- **Negativo**: `{key: "_neg_"}` (evita re-tentar)

### 2. Batch Fetching

**Problema**: 10 tokens = 10 requests sequenciais

**Solução**: Coletar únicos primeiro
```python
# Collect unique tokens
unique_tokens = set()
for tx in transactions:
    for output in tx['outputs']:
        for token in output.get('tokens', []):
            unique_tokens.add((token['policyId'], token['assetName']))

# Fetch metadata for all unique tokens
for policy_id, asset_name in unique_tokens:
    get_asset_metadata(policy_id, asset_name)

# Now all are cached, analyze transactions
for tx in transactions:
    analysis = analyze_transaction(tx)  # Uses cache
```

### 3. Early Returns

**Problema**: Verificar campos simples após HTTP request

**Solução**: Check simples primeiro
```python
def get_token_name(policy_id, asset_name_hex, fields):
    # 1. Check simple fields first (no HTTP)
    if fields.get('assetNameAscii'):
        return fields['assetNameAscii']
    
    # 2. Try hex decode (no HTTP)
    if asset_name_hex:
        decoded = decode_hex_ascii(asset_name_hex)
        if decoded:
            return decoded
    
    # 3. Only now fetch metadata (HTTP)
    if asset_name_hex:  # Only if there's a name to search
        metadata = get_asset_metadata(policy_id, asset_name_hex)
        if metadata:
            return extract_name(metadata)
    
    # 4. Fallback
    return f"Token {policy_id[:12]}..."
```

### 4. Paginação Reversa

**Problema**: Buscar página 1-20 para ver recentes

**Solução**: Buscar de trás para frente
```python
# Total de 42 páginas, quero 5 mais recentes
start_page = 42 - 5 + 1 = 38
# Buscar páginas: 42, 41, 40, 39, 38
```

**Resultado**: 80% menos páginas para ver transações atuais!

### 5. Ordenação no Cliente

**Problema**: API não garante ordem dentro da página

**Solução**: Sort após carregar
```python
# Sort by timestamp DESC
processed.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
```

---

## Casos de Uso

### Uso 1: Verificar Saldo de Wallet

**Cenário**: Admin quer verificar saldo da wallet do fundo antes de fazer swap.

**Passos**:
1. Ir para **Atividade → Cardano**
2. Endereço já pré-preenchido (default_address da API)
3. Tab **💰 Saldo e Tokens**
4. Ver ADA disponível e tokens nativos

**Resultado**: Decisão informada sobre quanto pode trocar.

---

### Uso 2: Acompanhar Recompensas de Staking

**Cenário**: Utilizador quer saber quanto ganhou de staking.

**Passos**:
1. **Atividade → Cardano**
2. Inserir endereço da wallet (ou selecionar de wallets salvas)
3. Tab **🎯 Staking**
4. Ver:
   - Pool delegado
   - Recompensas totais acumuladas
   - Disponíveis para levantar

**Resultado**: Transparência sobre earnings passivos.

---

### Uso 3: Auditar Transação Específica

**Cenário**: Alguém diz que enviou 100 ADA, admin quer confirmar.

**Passos**:
1. **Atividade → Cardano**
2. Endereço da wallet do fundo
3. Tab **📜 Transações**
4. Definir páginas = 1 (ver mais recentes)
5. Carregar transações
6. Procurar data/valor
7. Clicar em 🔍 CardanoScan para detalhes completos

**Resultado**: Confirmação rápida sem sair do dashboard.

---

### Uso 4: Configurar Nova API Key

**Cenário**: Rate limit atingido, precisa adicionar outra API.

**Passos**:
1. **Configurações → APIs Cardano**
2. Clicar **➕ Adicionar Nova API**
3. Preencher:
   - Nome: "CardanoScan Backup"
   - API Key: (sua nova key)
   - URL: https://api.cardanoscan.io/api/v1
4. Salvar
5. Desativar API antiga (se necessário)

**Resultado**: Sistema usa nova API automaticamente.

---

### Uso 5: Organizar Múltiplas Wallets

**Cenário**: Fundo tem wallet hot (operações) e cold (reserva).

**Passos**:
1. **Configurações → Wallets**
2. Adicionar wallet hot:
   - Nome: "Eternl Operações"
   - Tipo: hot
   - Blockchain: Cardano
   - Endereço: addr1...
   - Stake: stake1...
   - Marcar como principal
3. Adicionar wallet cold:
   - Nome: "Ledger Reserva"
   - Tipo: hardware
   - (Não marcar como principal)

**Resultado**: Consulta rápida de qualquer wallet, identificação clara.

---

## Troubleshooting

### Problema: "Nenhuma API Cardano configurada"

**Causa**: Tabela `t_api_cardano` vazia ou todas APIs inativas.

**Solução**:
1. Ir para **Configurações → APIs Cardano**
2. Adicionar nova API:
   - Obter key gratuita em: https://cardanoscan.io/api
   - Nome: "CardanoScan"
   - URL: `https://api.cardanoscan.io/api/v1`
3. Verificar que `is_active = TRUE`

---

### Problema: Token mostra como "Token 6df63e2f..."

**Causa**: Metadata não encontrado ou token sem metadata on-chain.

**Solução**:
1. **Se for token conhecido**: Adicionar em `TOKEN_DECIMALS_BY_POLICY`
   ```python
   TOKEN_DECIMALS_BY_POLICY = {
       "policy_id_aqui": decimals
   }
   ```

2. **Se tiver assetName**: Verificar se decodifica corretamente
   - Pode ser hex que não é ASCII válido
   
3. **Última opção**: Mostrar policyId (comportamento atual)

---

### Problema: Transações antigas mesmo com max_pages=1

**Causa**: (Já resolvido) Busca estava em ordem crescente.

**Solução Implementada**:
```python
# Buscar de trás para frente
for page in range(page_count, start_page - 1, -1):
    fetch_page(page)
```

**Verificar**: Deve ver transações de outubro/novembro com 1 página.

---

### Problema: Erro 429 (Rate Limit)

**Causa**: Muitas requests em pouco tempo.

**Soluções**:
1. **Aumentar timeout entre requests**:
   ```python
   import time
   time.sleep(0.1)  # 100ms entre requests
   ```

2. **Usar cache mais agressivo**:
   - Não limpar `_asset_meta_cache` durante sessão
   - Considerar cache persistente (Redis/DB)

3. **Adicionar segunda API key**:
   - Configurar em **APIs Cardano**
   - Sistema rotaciona automaticamente (futuro)

---

### Problema: Stake address não mostra info

**Causa**: Endereço `addr1...` não `stake1...`

**Solução**:
- Para staking info, API aceita `addr1...` ou `stake1...`
- Se tiver ambos salvos na wallet, usar `stake_address`
- Se só tiver `addr1...`, API deriva automaticamente

**Verificar**: Campo `stake_address` preenchido em **Configurações → Wallets**

---

### Problema: IBAN inválido ao adicionar banco

**Causa**: Formato incorreto ou espaços/caracteres especiais.

**Solução**:
- IBAN deve ter: 2 letras (país) + 2 dígitos + até 30 alfanuméricos
- Remover espaços e hífen
- Exemplo válido: `PT50001234567890123456789`
- Validação é básica, não verifica checksum completo

---

## Próximos Passos

### Features Planejadas

- [ ] **Dropdown de Wallets**: Selecionar wallet salva em vez de digitar endereço
- [ ] **Auto-sync de Balances**: Cronjob para atualizar saldos periodicamente
- [ ] **Rotação de APIs**: Usar múltiplas APIs automaticamente
- [ ] **Cache Persistente**: Salvar metadados em DB
- [ ] **Transaction Filters**: Filtrar por tipo, data, valor
- [ ] **Export Transactions**: CSV/PDF de histórico
- [ ] **Notificações**: Alertas de transações recebidas
- [ ] **Multi-blockchain**: Ethereum, Bitcoin explorers

### Melhorias de Performance

- [ ] GraphQL para batch requests (se API suportar)
- [ ] WebSocket para updates em tempo real
- [ ] Service worker para cache offline
- [ ] Lazy loading de transações antigas

---

## Recursos Externos

### APIs e Documentação

- [CardanoScan API v1 Docs](https://docs.cardanoscan.io/)
- [CIP-25 - NFT Metadata Standard](https://cips.cardano.org/cips/cip25/)
- [Cardano Addresses Explained](https://docs.cardano.org/new-to-cardano/cardano-addresses)

### Tools

- [CardanoScan Explorer](https://cardanoscan.io)
- [Bech32 Converter](https://slowli.github.io/bech32-buffer/)
- [Cardano Explorer (IOG)](https://explorer.cardano.org/)

### Código Relacionado

- `services/cardano_api.py` - Cliente API
- `pages/cardano.py` - Interface Streamlit
- `database/wallets.py` - CRUD wallets
- `database/banks.py` - CRUD bancos
- `database/api_config.py` - CRUD APIs

---

**[← Voltar à Wiki](README.md)** | **[↑ Topo](#-integração-blockchain-cardano)**
