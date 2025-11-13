# Debug Scripts

Esta pasta contém scripts de debug e manutenção utilizados durante o desenvolvimento do CryptoDashboard.

## Scripts de Verificação

- **check_addresses.py**: Verifica endereços e transações mal associadas entre wallets
- **check_djed_prices.py**: Verifica configuração e snapshots de preços do DJED
- **check_wallet_ids.py**: Verifica wallet_ids e procura por duplicados em transações

## Scripts de Comparação

- **compare_cardanoscan_transactions.py**: Compara transações entre API CardanoScan e base de dados

## Scripts de Correção

- **fix_cross_wallet_txs.py**: Corrige transações cruzadas entre wallets (antes da migração composite PK)
- **fix_djedmicrousd.py**: Configura DjedMicroUSD para usar preço do DJED
- **update_djedmicrousd.py**: Atualiza entradas existentes de DJEDMICROUSD

## Scripts de Sincronização

- **sync_wallet2_fix.py**: Sincronização manual para wallet específica com mais páginas
- **get_wallet2_address.py**: Obtém endereço de wallet da base de dados

## Scripts de Preços

- **fill_djed_snapshots.py**: Preenche snapshots históricos para ativos baseados em DJED
- **test_coingecko_api_key.py**: Verifica uso correto da API key do CoinGecko
- **test_history_fallback.py**: Testa fallback de market_chart para preços históricos
- **update_coingecko_key.py**: Atualiza API key do CoinGecko na base de dados

## Scripts de Debug de Transações

- **debug_missing_tx.py**: Investiga transações específicas que parecem estar em falta

## Nota

Estes scripts foram criados para debugging e manutenção durante o desenvolvimento. 
Muitos podem estar desatualizados após mudanças no schema ou lógica da aplicação.
Use com cuidado em ambiente de produção.
