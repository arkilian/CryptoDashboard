# 📚 Guia do Novo Modelo de Transações V2

## 🎯 Objetivo

Suportar todas as operações de cripto: depósitos, levantamentos, compras, vendas, swaps, transferências entre contas, staking, lending, borrowing, etc.

## 📊 Estrutura da Transação V2

### Colunas Principais

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `transaction_type` | TEXT | Tipo de operação (ver tabela abaixo) |
| `from_asset_id` | INT | Asset de origem (o que sai) |
| `from_quantity` | DECIMAL | Quantidade que sai |
| `from_account_id` | INT | Conta de origem (para transfers) |
| `to_asset_id` | INT | Asset de destino (o que entra) |
| `to_quantity` | DECIMAL | Quantidade que entra |
| `to_account_id` | INT | Conta de destino (para transfers) |
| `account_id` | INT | Conta principal da operação |
| `fee_asset_id` | INT | Asset usado para pagar fee |
| `fee_quantity` | DECIMAL | Quantidade de fee |
| `fee_eur` | DECIMAL | Fee em EUR (legacy, ainda suportado) |

### Colunas Legacy (Retrocompatibilidade)

Mantidas para compatibilidade com código antigo:
- `asset_id`: usado em `buy`/`sell`
- `quantity`: quantidade em `buy`/`sell`
- `price_eur`: preço unitário em EUR
- `total_eur`: valor total em EUR

---

## 🔄 Tipos de Transação

### 1. **DEPOSIT** (banco → exchange)
Depositar EUR do banco para uma exchange.

```python
{
    'transaction_type': 'deposit',
    'from_asset_id': EUR_id,
    'from_quantity': 1000.00,
    'from_account_id': conta_banco_id,
    'to_asset_id': EUR_id,
    'to_quantity': 1000.00,
    'to_account_id': binance_spot_id,
    'fee_eur': 0.00
}
```

**Holdings Impact:**
- Banco: -1000 EUR
- Binance Spot: +1000 EUR

---

### 2. **WITHDRAWAL** (exchange → banco)
Levantar EUR da exchange para o banco.

```python
{
    'transaction_type': 'withdrawal',
    'from_asset_id': EUR_id,
    'from_quantity': 500.00,
    'from_account_id': binance_spot_id,
    'to_asset_id': EUR_id,
    'to_quantity': 500.00,
    'to_account_id': conta_banco_id,
    'fee_eur': 0.00
}
```

**Holdings Impact:**
- Binance Spot: -500 EUR
- Banco: +500 EUR

---

### 3. **BUY** (EUR → Cripto)
Comprar cripto com EUR.

```python
{
    'transaction_type': 'buy',
    'from_asset_id': EUR_id,
    'from_quantity': 100.00,
    'to_asset_id': ADA_id,
    'to_quantity': 50.00,
    'account_id': binance_spot_id,
    'fee_asset_id': EUR_id,
    'fee_quantity': 0.50,
    # Legacy (ainda preenchido para retrocompat):
    'asset_id': ADA_id,
    'quantity': 50.00,
    'price_eur': 2.00,
    'total_eur': 100.00,
    'fee_eur': 0.50
}
```

**Holdings Impact:**
- Binance Spot: -100.50 EUR, +50 ADA

---

### 4. **SELL** (Cripto → EUR)
Vender cripto por EUR.

```python
{
    'transaction_type': 'sell',
    'from_asset_id': ADA_id,
    'from_quantity': 25.00,
    'to_asset_id': EUR_id,
    'to_quantity': 49.50,
    'account_id': binance_spot_id,
    'fee_asset_id': EUR_id,
    'fee_quantity': 0.50,
    # Legacy:
    'asset_id': ADA_id,
    'quantity': 25.00,
    'price_eur': 2.00,
    'total_eur': 50.00,
    'fee_eur': 0.50
}
```

**Holdings Impact:**
- Binance Spot: -25 ADA, +49.50 EUR

---

### 5. **SWAP** (Cripto A → Cripto B)
Trocar um ativo por outro (DEX, exchange).

```python
{
    'transaction_type': 'swap',
    'from_asset_id': ADA_id,
    'from_quantity': 50.00,
    'to_asset_id': USDC_id,
    'to_quantity': 40.00,
    'account_id': minswap_id,
    'fee_asset_id': ADA_id,
    'fee_quantity': 0.50
}
```

**Holdings Impact:**
- Minswap: -50.50 ADA, +40 USDC

---

### 6. **TRANSFER** (Conta A → Conta B)
Mover asset entre contas/wallets.

```python
{
    'transaction_type': 'transfer',
    'from_asset_id': ADA_id,
    'from_quantity': 100.00,
    'from_account_id': binance_spot_id,
    'to_asset_id': ADA_id,
    'to_quantity': 99.50,
    'to_account_id': metamask_id,
    'fee_asset_id': ADA_id,
    'fee_quantity': 0.50
}
```

**Holdings Impact:**
- Binance Spot: -100 ADA
- MetaMask: +99.50 ADA
- (0.50 ADA perdido em network fee)

---

### 7. **STAKE** (Disponível → Staked)
Colocar asset em staking/earn.

```python
{
    'transaction_type': 'stake',
    'from_asset_id': ADA_id,
    'from_quantity': 100.00,
    'from_account_id': binance_spot_id,
    'to_asset_id': ADA_id,
    'to_quantity': 100.00,
    'to_account_id': binance_earn_id,
    'fee_quantity': 0.00
}
```

**Holdings Impact:**
- Binance Spot: -100 ADA
- Binance Earn: +100 ADA

---

### 8. **UNSTAKE** (Staked → Disponível)
Remover asset de staking/earn.

```python
{
    'transaction_type': 'unstake',
    'from_asset_id': ADA_id,
    'from_quantity': 102.00,  # Original + rewards
    'from_account_id': binance_earn_id,
    'to_asset_id': ADA_id,
    'to_quantity': 102.00,
    'to_account_id': binance_spot_id,
    'fee_quantity': 0.00
}
```

**Holdings Impact:**
- Binance Earn: -102 ADA
- Binance Spot: +102 ADA

---

### 9. **REWARD** (Recompensa Recebida)
Receber recompensas de staking, airdrops, etc.

```python
{
    'transaction_type': 'reward',
    'to_asset_id': ADA_id,
    'to_quantity': 2.00,
    'to_account_id': binance_earn_id,
    # from_* fica NULL (é criação de valor)
}
```

**Holdings Impact:**
- Binance Earn: +2 ADA

---

### 10. **LEND** (Fornecer Liquidez)
Emprestar asset a um protocolo DeFi.

```python
{
    'transaction_type': 'lend',
    'from_asset_id': USDC_id,
    'from_quantity': 1000.00,
    'from_account_id': metamask_id,
    'to_asset_id': USDC_id,  # Ou LP token
    'to_quantity': 1000.00,
    'to_account_id': aave_id,
    'fee_asset_id': ETH_id,
    'fee_quantity': 0.001  # Gas fee
}
```

**Holdings Impact:**
- MetaMask: -1000 USDC, -0.001 ETH
- Aave: +1000 USDC

---

### 11. **BORROW** (Pedir Emprestado)
Receber asset emprestado de protocolo DeFi.

```python
{
    'transaction_type': 'borrow',
    'to_asset_id': USDC_id,
    'to_quantity': 500.00,
    'to_account_id': metamask_id,
    'fee_asset_id': ETH_id,
    'fee_quantity': 0.001
    # from_* fica NULL (é dívida)
}
```

**Holdings Impact:**
- MetaMask: +500 USDC, -0.001 ETH
- ⚠️ Nota: Este modelo não rastreia dívidas automaticamente!

---

### 12. **REPAY** (Pagar Empréstimo)
Devolver asset emprestado + juros.

```python
{
    'transaction_type': 'repay',
    'from_asset_id': USDC_id,
    'from_quantity': 550.00,  # Principal + juros
    'from_account_id': metamask_id,
    'fee_asset_id': ETH_id,
    'fee_quantity': 0.001
}
```

**Holdings Impact:**
- MetaMask: -550 USDC, -0.001 ETH

---

### 13. **LIQUIDATE** (Liquidação)
Perda de colateral por liquidação.

```python
{
    'transaction_type': 'liquidate',
    'from_asset_id': ETH_id,
    'from_quantity': 1.00,
    'from_account_id': aave_id
}
```

**Holdings Impact:**
- Aave: -1 ETH

---

## 📐 Cálculo de Holdings por Conta

### Fórmula

Para cada `(asset_id, account_id)`:

```python
holdings = Σ (to_quantity) - Σ (from_quantity) - Σ (fee_quantity if fee_asset_id matches)
```

### Exemplo Completo

**Transações:**
1. Deposit: 1000 EUR (banco → Binance Spot)
2. Buy: 100 EUR → 50 ADA (Binance Spot)
3. Transfer: 50 ADA (Binance Spot → MetaMask), fee 0.5 ADA
4. Stake: 49.5 ADA (MetaMask → MetaMask Staking Pool)
5. Reward: +2 ADA (MetaMask Staking Pool)

**Holdings Finais:**
- Banco: -1000 EUR
- Binance Spot: +900 EUR (1000 - 100)
- Binance Spot: 0 ADA (50 comprado - 50 transferido)
- MetaMask: 0 ADA (49.5 recebido - 49.5 staked)
- MetaMask Staking: 51.5 ADA (49.5 staked + 2 reward)

---

## 🧮 Cálculo de Saldo Total (EUR)

### Fórmula

```python
saldo_total_eur = Σ (holdings_qty × current_price_eur) para todos os assets
```

Onde:
- `holdings_qty` calculado como acima
- `current_price_eur` buscado do CoinGecko ou snapshots

### Por Conta

Para análise detalhada, calcular por conta:

```python
saldo_binance_spot = 900 EUR + (0 ADA × 2.00) = 900 EUR
saldo_metamask_staking = (51.5 ADA × 2.00) = 103 EUR
saldo_total = 1003 EUR
```

---

## 🚀 Workflow Típico

### Cenário 1: Comprar e Stakear ADA

```
1. DEPOSIT: 1000 EUR (banco → Binance)
2. BUY: 100 EUR → 50 ADA (Binance Spot)
3. STAKE: 50 ADA (Binance Spot → Binance Earn)
4. REWARD: +2 ADA (Binance Earn)
5. UNSTAKE: 52 ADA (Binance Earn → Binance Spot)
```

**Resultado:**
- Banco: -1000 EUR
- Binance Spot: 900 EUR + 52 ADA

---

### Cenário 2: Swap em DEX

```
1. DEPOSIT: 1000 EUR (banco → Binance)
2. BUY: 1000 EUR → 500 ADA (Binance Spot)
3. TRANSFER: 500 ADA (Binance → MetaMask), fee 0.5 ADA
4. SWAP: 499.5 ADA → 400 USDC (MetaMask/Minswap), fee 0.2 ADA
```

**Resultado:**
- Banco: -1000 EUR
- Binance Spot: 0 EUR, 0 ADA
- MetaMask: 0 ADA (-499.5 de swap - 0.2 de fee)
- MetaMask: 400 USDC

---

### Cenário 3: Lending DeFi

```
1. DEPOSIT: 1000 EUR (banco → Binance)
2. BUY: 1000 EUR → 1000 USDC (Binance)
3. TRANSFER: 1000 USDC (Binance → MetaMask), fee 1 USDC
4. LEND: 999 USDC (MetaMask → Aave), gas 0.001 ETH
```

**Resultado:**
- Banco: -1000 EUR
- Binance: 0 EUR, 0 USDC
- MetaMask: 0 USDC, -0.001 ETH
- Aave: 999 USDC (em lending)

---

## ⚠️ Notas Importantes

### 1. EUR é um Asset
EUR agora está na tabela `t_assets` como `is_stablecoin=TRUE`.

### 2. Conta "Banco"
Existe uma exchange especial "Banco" (categoria FIAT) para rastrear EUR fora de exchanges.

### 3. Retrocompatibilidade
Transações antigas `buy`/`sell` continuam funcionando:
- As colunas legacy (`asset_id`, `quantity`, `price_eur`, `total_eur`) são mantidas.
- A migration preenche automaticamente `from_*`/`to_*` para transações antigas.

### 4. Fees em Qualquer Asset
Fees agora podem ser em qualquer asset (não apenas EUR):
- Use `fee_asset_id` + `fee_quantity` para fees em cripto
- `fee_eur` ainda funciona para fees em EUR (retrocompat)

### 5. Holdings por Conta
Para saber "onde está" cada asset, sempre use `account_id` nas queries:
```sql
SELECT a.symbol, ea.name AS account, SUM(...)
FROM t_transactions t
JOIN t_assets a ON ...
LEFT JOIN t_exchange_accounts ea ON t.account_id = ea.account_id
GROUP BY a.symbol, ea.name
```

### 6. Dívidas (Borrow/Repay)
O modelo atual **NÃO rastreia automaticamente dívidas**. Se precisares:
- Criar tabela separada `t_loans` para rastrear empréstimos ativos
- Ou calcular manualmente: `borrow - repay` por protocolo

---

## 🛠️ Setup

A tabela `t_transactions` com todas as colunas V2 (e legado compatível) é criada no ficheiro `database/tablesv2.sql`. Para inicializar o ambiente, aplique esse ficheiro ao PostgreSQL:

```bash
psql -U crypto_user -d crypto_dashboard -f database/tablesv2.sql
```

Isso criará todas as tabelas, colunas, índices necessários, bem como inserirá o asset EUR e a exchange especial "Banco". Não há migrações em runtime; o schema é gerido manualmente ou através de novos scripts SQL conforme necessário.

## 📋 Próximos Passos

1. ✅ Migration criada
2. ⏳ Atualizar UI de registo de transações
3. ⏳ Atualizar cálculo de holdings
4. ⏳ Atualizar histórico de transações
5. ⏳ Atualizar análise de portfólio
6. ⏳ Testar com cenários reais

---

**Última atualização:** 2025-11-01
