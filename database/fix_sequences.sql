-- ========================================
-- FIX SEQUENCES - Resetar sequences após importação de dados
-- ========================================
-- Este script atualiza todas as sequences para o próximo valor disponível
-- Resolve o erro: "duplicate key value violates unique constraint"
-- ========================================

SELECT setval('t_users_user_id_seq', (SELECT COALESCE(MAX(user_id), 1) FROM t_users), true);
SELECT setval('t_gender_gender_id_seq', (SELECT COALESCE(MAX(gender_id), 1) FROM t_gender), true);
SELECT setval('t_address_address_id_seq', (SELECT COALESCE(MAX(address_id), 1) FROM t_address), true);
SELECT setval('t_user_profile_profile_id_seq', (SELECT COALESCE(MAX(profile_id), 1) FROM t_user_profile), true);
SELECT setval('t_fee_settings_setting_id_seq', (SELECT COALESCE(MAX(setting_id), 1) FROM t_fee_settings), true);
SELECT setval('t_user_fees_fee_id_seq', (SELECT COALESCE(MAX(fee_id), 1) FROM t_user_fees), true);
SELECT setval('t_exchanges_exchange_id_seq', (SELECT COALESCE(MAX(exchange_id), 1) FROM t_exchanges), true);
SELECT setval('t_assets_asset_id_seq', (SELECT COALESCE(MAX(asset_id), 1) FROM t_assets), true);
SELECT setval('t_exchange_accounts_account_id_seq', (SELECT COALESCE(MAX(account_id), 1) FROM t_exchange_accounts), true);
SELECT setval('t_user_capital_movements_movement_id_seq', (SELECT COALESCE(MAX(movement_id), 1) FROM t_user_capital_movements), true);
SELECT setval('t_transactions_transaction_id_seq', (SELECT COALESCE(MAX(transaction_id), 1) FROM t_transactions), true);
SELECT setval('t_price_snapshots_snapshot_id_seq', (SELECT COALESCE(MAX(snapshot_id), 1) FROM t_price_snapshots), true);
SELECT setval('t_portfolio_snapshots_snapshot_id_seq', (SELECT COALESCE(MAX(snapshot_id), 1) FROM t_portfolio_snapshots), true);
SELECT setval('t_portfolio_holdings_holding_id_seq', (SELECT COALESCE(MAX(holding_id), 1) FROM t_portfolio_holdings), true);
SELECT setval('t_user_snapshots_user_snapshot_id_seq', (SELECT COALESCE(MAX(user_snapshot_id), 1) FROM t_user_snapshots), true);
SELECT setval('t_user_manual_snapshots_snapshot_id_seq', (SELECT COALESCE(MAX(snapshot_id), 1) FROM t_user_manual_snapshots), true);
SELECT setval('t_snapshot_assets_id_seq', (SELECT COALESCE(MAX(id), 1) FROM t_snapshot_assets), true);
SELECT setval('t_tags_tag_id_seq', (SELECT COALESCE(MAX(tag_id), 1) FROM t_tags), true);
SELECT setval('t_user_shares_share_id_seq', (SELECT COALESCE(MAX(share_id), 1) FROM t_user_shares), true);
SELECT setval('t_wallet_wallet_id_seq', (SELECT COALESCE(MAX(wallet_id), 1) FROM t_wallet), true);
SELECT setval('t_banco_banco_id_seq', (SELECT COALESCE(MAX(banco_id), 1) FROM t_banco), true);
SELECT setval('t_api_coingecko_api_id_seq', (SELECT COALESCE(MAX(api_id), 1) FROM t_api_coingecko), true);
SELECT setval('t_api_cardano_api_id_seq', (SELECT COALESCE(MAX(api_id), 1) FROM t_api_cardano), true);
SELECT setval('t_cardano_tx_io_io_id_seq', (SELECT COALESCE(MAX(io_id), 1) FROM t_cardano_tx_io), true);

-- Verificação (opcional)
-- Mostra o próximo valor de cada sequence
SELECT 'Sequences atualizadas com sucesso!' as status;
