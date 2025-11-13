# 📈 Portfolio v3 (Cardano · DB-first)

Este módulo introduz:
- Tabelas relacionais para transações Cardano (t_cardano_transactions, t_cardano_tx_io, t_cardano_assets, t_cardano_sync_state)
- Serviço de sincronização `services/cardano_sync.py`
- Nova página Streamlit `pages/portfolio_v3.py`

## 🗃️ Migração

Aplicar o ficheiro SQL:
- `database/migrations/20251103_cardano_tx_v3.sql`

Cria as novas tabelas e índices necessários para persistir transações Cardano.

## 🔌 API & Wallets

- Configura a API do CardanoScan em `t_api_cardano` (ver `database/new_tables.sql` e página de Configurações → APIs Cardano)
- Regista as wallets Cardano em `t_wallet` (Configurações → Wallets)

## 🔄 Sincronização (On-demand)

Na página `Portfólio v3`:
- Lê SEMPRE do DB primeiro
- Botão "Sincronizar Transações Cardano" para buscar novas transações e gravar no DB

## 📊 Gráfico

O gráfico usa:
- Deltas diários de ADA/tokens (DB) → holdings acumulados
- Preços históricos (CoinGecko snapshots) → valorização em EUR
- Movimentos de capital do utilizador (`t_user_capital_movements`) → caixa (EUR)

## 🔍 Notas

- Tokens desconhecidos sem preço no CoinGecko terão valor 0 no gráfico
- ADA é convertido de lovelace para ADA (1 ADA = 1_000_000 lovelace)
- Esta versão não projeta para `t_transactions` V2; o cálculo é direto das tabelas Cardano
