# Cardano API - Otimizações de Performance

## Resumo das Otimizações Implementadas

### 1. Cache Negativo para Metadata
**Problema:** Quando um token não tem metadata disponível na API, fazíamos pedidos repetidos desnecessários.

**Solução:** Guardamos em cache quando uma consulta falha (`_neg_{cache_key}`), evitando novas tentativas para o mesmo token.

**Impacto:** Reduz drasticamente chamadas HTTP para tokens sem metadata (ex: tokens custom, NFTs sem info).

### 2. Batch de Metadata por Transação
**Problema:** Chamávamos `get_asset_metadata()` para cada ocorrência de token (inputs + outputs), resultando em chamadas duplicadas.

**Solução:** Coletamos primeiro todos os tokens únicos da transação (`unique_tokens`), depois fazemos batch das chamadas de metadata.

**Impacto:** Se uma transação envolve o mesmo token em múltiplos inputs/outputs, só fazemos 1 pedido HTTP em vez de N.

### 3. Early Returns em `get_token_name()`
**Problema:** Verificávamos metadata ANTES de campos simples (ticker, symbol), causando chamadas HTTP desnecessárias.

**Solução:** Reordenamos a lógica:
1. Verificar campos diretos não-hex (ticker, symbol, tokenName) → **early return**
2. Só depois tentar metadata do explorer
3. Fallback para decodificação hex e policyId

**Impacto:** Tokens com ticker/symbol definidos não geram chamadas HTTP; resposta instantânea.

### 4. Verificação de assetName Antes de Metadata
**Problema:** Fazíamos pedidos de metadata mesmo quando `assetName` era vazio/None.

**Solução:** Só chamamos `get_asset_metadata()` se `asset_hex` existir.

**Impacto:** Tokens sem assetName (como qDJED) não geram pedidos HTTP falhados.

### 5. Cache In-Memory Persistente
**Já implementado:** Cache de metadata na instância de `CardanoScanAPI` durante toda a sessão Streamlit.

**Benefício:** Segunda vez que vês uma transação com os mesmos tokens → **0 chamadas HTTP**.

## Métricas Esperadas

### Antes das Otimizações
- 50 transações com 2 tokens cada = ~200 chamadas HTTP de metadata (repetidas)
- Tokens sem metadata = pedidos falhados repetidos
- Tempo de carregamento: ~10-15 segundos

### Depois das Otimizações
- 50 transações com 2 tokens únicos = 2 chamadas HTTP de metadata (batch + cache)
- Tokens sem metadata = 1 tentativa, depois cache negativo
- Tempo de carregamento: **~2-3 segundos** (redução de 70-80%)

### Cache Hit Rate
- Primeira carga: cache miss (chamadas normais)
- Atualizações subsequentes: **~90-95% cache hit** (quase instantâneo)

## Recomendações Adicionais

### Se ainda for lento:
1. **Reduzir páginas de transações:** Começar com 1-2 páginas em vez de 5
2. **Timeout menor:** Alterar timeout de 10s para 5s em `_try_fetch()`
3. **Desabilitar metadata lookup:** Comentar `get_asset_metadata()` e usar apenas policyId para tokens desconhecidos

### Para máxima velocidade:
```python
# Desabilitar metadata completamente (só usar mapeamentos estáticos)
def get_asset_metadata(self, policy_id, asset_name_hex):
    return None  # Forçar fallback para policyId
```

## Estado Atual
✅ Cache positivo e negativo  
✅ Batch de metadata por transação  
✅ Early returns em resolução de nomes  
✅ Verificação de assetName antes de HTTP  
✅ Cache in-memory persistente

**Performance geral:** Excelente para cargas típicas (1-5 páginas, ~100 transações).
