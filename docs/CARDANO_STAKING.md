# Cardano Staking - Documentação

## Visão Geral

A funcionalidade de staking no Crypto Dashboard permite visualizar informações detalhadas sobre delegação de ADA e recompensas de staking para qualquer endereço Cardano.

## Endpoints API

### `GET /account/info`

Consulta informações de staking de uma conta Cardano via CardanoScan API.

**Parâmetros:**
- `address` (string, required): Endereço Cardano no formato bech32 (addr1...)

**Response Success (200):**
```json
{
  "stakeAddress": "stake1u9...",
  "poolId": "pool1...",
  "poolName": "Nome da Pool",
  "poolTicker": "TICKER",
  "delegated": true,
  "rewards": 123456789,
  "withdrawals": 50000000,
  "controlledStake": 1000000000
}
```

**Response Error (404):**
Conta de staking não encontrada ou não registada.

## Estrutura de Dados

### `get_stake_info()` - CardanoScanAPI

Retorna tupla `(dados, erro)` onde `dados` contém:

```python
{
    "stake_address": str,           # Endereço de staking (stake1...)
    "pool_id": str,                  # ID da pool delegada
    "pool_name": str,                # Nome da pool
    "pool_ticker": str,              # Ticker/símbolo da pool
    "is_delegated": bool,            # True se delegado a uma pool
    "rewards_lovelace": int,         # Total de recompensas em lovelace
    "rewards_ada": float,            # Total de recompensas em ADA
    "withdrawals_lovelace": int,     # Total retirado em lovelace
    "withdrawals_ada": float,        # Total retirado em ADA
    "available_rewards_ada": float,  # Recompensas disponíveis (rewards - withdrawals)
    "controlled_stake_lovelace": int,# ADA em stake (lovelace)
    "controlled_stake_ada": float    # ADA em stake (ADA)
}
```

## Interface do Utilizador

### Tab "🎯 Staking"

Localizada entre "💰 Saldo e Tokens" e "📜 Transações".

#### Conta Delegada (is_delegated = True)

**Secção: Delegação Atual**
- Pool Name / Ticker
- Pool ID (com link para PoolTool)

**Secção: Recompensas**
- **Total Recompensas**: Acumulado desde o início
- **Já Retiradas**: Quantia já movida para a wallet
- **Disponíveis**: Pronto para retirar (com indicador visual 🟢)

**Secção: Stake Controlado**
- ADA em Stake: Total delegado à pool

**Secção: Stake Address**
- Endereço de staking completo (monospace)

#### Conta Não Delegada (is_delegated = False)

**Guia de Início:**
1. Como começar a fazer staking
2. Passo a passo (wallet → staking → escolha de pool → delegação)
3. Benefícios do staking:
   - ~3-5% APY
   - ADA permanece na wallet
   - Sem lock-up
   - Descentralização da rede

#### Sem Conta de Staking (404)

Mensagem informativa indicando que o endereço não tem conta de staking registada.

## Conversões e Cálculos

### Lovelace ↔ ADA
```python
1 ADA = 1,000,000 lovelace
ada = lovelace / 1_000_000
```

### Recompensas Disponíveis
```python
available_rewards_ada = (rewards - withdrawals) / 1_000_000
```

## Integração com Explorers

### PoolTool
Link direto para detalhes da pool:
```
https://pooltool.io/pool/{pool_id}
```

### CardanoScan
Endereço de staking pode ser consultado em:
```
https://cardanoscan.io/stakeKey/{stake_address}
```

## Estados Possíveis

| Estado | Condição | UI |
|--------|----------|-----|
| **Delegado Ativo** | `is_delegated = True` | ✅ Status verde, métricas completas, pool info |
| **Não Delegado** | `is_delegated = False` | ℹ️ Guia de início, benefícios |
| **Sem Staking** | API 404 | ⚠️ Mensagem informativa, conta não registada |
| **Erro API** | Timeout/Erro | ❌ Mensagem de erro |

## Performance e Cache

- **Cache**: Não implementado (dados sempre frescos da API)
- **Timeout**: 10 segundos por pedido
- **Retry**: Não implementado

### Recomendações de Otimização

Para melhorar performance em caso de múltiplas consultas:

1. **Cache temporal**: Guardar stake_info por 5 minutos
2. **Batch requests**: Se consultar múltiplos endereços
3. **Lazy loading**: Carregar tab de staking apenas quando selecionada

```python
# Exemplo de cache simples (não implementado)
if "stake_cache" not in st.session_state:
    st.session_state.stake_cache = {}

cache_key = f"{address}_stake"
cache_time = 300  # 5 minutos

if cache_key in st.session_state.stake_cache:
    cached_data, timestamp = st.session_state.stake_cache[cache_key]
    if time.time() - timestamp < cache_time:
        stake_data = cached_data
    else:
        stake_data, error = api.get_stake_info(address)
        st.session_state.stake_cache[cache_key] = (stake_data, time.time())
```

## Métricas de Negócio

### APY (Annual Percentage Yield)

Cardano staking oferece aproximadamente **3-5% APY**, dependendo de:
- Performance da pool
- Saturation da pool
- Taxas da pool (margin + fixed fee)
- Participação ativa na rede

### Custos de Delegação

- **Primeira delegação**: ~2 ADA (depósito) + transaction fee
- **Re-delegação**: Apenas transaction fee (~0.17 ADA)
- **Withdrawal**: Transaction fee (~0.17 ADA)

O depósito de 2 ADA é **reembolsável** ao desregistar a stake key.

### Ciclo de Recompensas

```
Epoch N: Delega → Epoch N+2: Snapshot → Epoch N+4: Recompensas disponíveis
```

Demora **15-20 dias** (~3 epochs) para começar a receber recompensas após primeira delegação.

## Glossário

| Termo | Descrição |
|-------|-----------|
| **Stake Address** | Endereço especial (stake1...) associado à conta de staking |
| **Pool ID** | Identificador único da stake pool |
| **Delegation** | Processo de associar ADA a uma stake pool |
| **Rewards** | Recompensas acumuladas por participar no staking |
| **Withdrawals** | Recompensas já movidas para a wallet principal |
| **Controlled Stake** | Quantidade de ADA efetivamente delegado |
| **Epoch** | Período de tempo na blockchain Cardano (~5 dias) |
| **Saturation** | Limite máximo de stake que uma pool pode ter para manter ROI ótimo |

## Troubleshooting

### "Conta de staking não encontrada"
**Causa:** Endereço nunca delegou ou não tem stake key registada.
**Solução:** Verificar se o endereço está correto; consultar wallet para registar stake key.

### "Timeout ao consultar informações de staking"
**Causa:** API CardanoScan lenta ou indisponível.
**Solução:** Tentar novamente; verificar status da API.

### Recompensas disponíveis = 0 mas já delegou
**Causa:** Ainda dentro do período de espera (3 epochs).
**Solução:** Aguardar 15-20 dias após primeira delegação.

### Pool sem nome/ticker
**Causa:** Pool não registou metadata on-chain.
**Solução:** Normal; usar Pool ID para identificação.

## Segurança

⚠️ **IMPORTANTE**: Esta funcionalidade é **read-only**. Não permite:
- Delegar ADA
- Retirar recompensas
- Alterar pool
- Desregistar stake key

Para essas operações, utilize sempre a sua wallet oficial (Daedalus, Yoroi, Eternl, etc.).

## Recursos Externos

- [Cardano Staking Guide](https://cardano.org/stake-pool-delegation/)
- [CardanoScan API Docs](https://docs.cardanoscan.io)
- [PoolTool](https://pooltool.io)
- [Pool.pm](https://pool.pm)
- [Adapools](https://adapools.org)

## Roadmap / Melhorias Futuras

- [ ] Histórico de recompensas por epoch
- [ ] Gráfico de evolução de rewards
- [ ] Comparação de pools (ROI, fees, performance)
- [ ] Alertas de mudança de pool ou saturação
- [ ] Export de dados fiscais (rewards por ano)
- [ ] Calculadora de ROI estimado
- [ ] Integração com Koios API (alternativa ao CardanoScan)
