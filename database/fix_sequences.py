"""
Script para resetar sequences após importação de dados
Resolve erro: duplicate key value violates unique constraint
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT')
)

sequences = [
    ('t_users_user_id_seq', 't_users', 'user_id'),
    ('t_gender_gender_id_seq', 't_gender', 'gender_id'),
    ('t_address_address_id_seq', 't_address', 'address_id'),
    ('t_user_profile_profile_id_seq', 't_user_profile', 'profile_id'),
    ('t_fee_settings_setting_id_seq', 't_fee_settings', 'setting_id'),
    ('t_user_fees_fee_id_seq', 't_user_fees', 'fee_id'),
    ('t_exchanges_exchange_id_seq', 't_exchanges', 'exchange_id'),
    ('t_assets_asset_id_seq', 't_assets', 'asset_id'),
    ('t_exchange_accounts_account_id_seq', 't_exchange_accounts', 'account_id'),
    ('t_user_capital_movements_movement_id_seq', 't_user_capital_movements', 'movement_id'),
    ('t_transactions_transaction_id_seq', 't_transactions', 'transaction_id'),
    ('t_price_snapshots_snapshot_id_seq', 't_price_snapshots', 'snapshot_id'),
    ('t_portfolio_snapshots_snapshot_id_seq', 't_portfolio_snapshots', 'snapshot_id'),
    ('t_portfolio_holdings_holding_id_seq', 't_portfolio_holdings', 'holding_id'),
    ('t_user_snapshots_user_snapshot_id_seq', 't_user_snapshots', 'user_snapshot_id'),
    ('t_user_manual_snapshots_snapshot_id_seq', 't_user_manual_snapshots', 'snapshot_id'),
    ('t_snapshot_assets_id_seq', 't_snapshot_assets', 'id'),
    ('t_tags_tag_id_seq', 't_tags', 'tag_id'),
    ('t_user_shares_share_id_seq', 't_user_shares', 'share_id'),
    ('t_wallet_wallet_id_seq', 't_wallet', 'wallet_id'),
    ('t_banco_banco_id_seq', 't_banco', 'banco_id'),
    ('t_api_coingecko_api_id_seq', 't_api_coingecko', 'api_id'),
    ('t_api_cardano_api_id_seq', 't_api_cardano', 'api_id'),
    ('t_cardano_tx_io_io_id_seq', 't_cardano_tx_io', 'io_id'),
]

cur = conn.cursor()

print("=" * 70)
print("RESETAR SEQUENCES")
print("=" * 70)
print()

for seq_name, table_name, col_name in sequences:
    try:
        cur.execute(f"SELECT setval('{seq_name}', (SELECT COALESCE(MAX({col_name}), 1) FROM {table_name}), true)")
        result = cur.fetchone()[0]
        print(f"✓ {seq_name:45s} → {result}")
    except Exception as e:
        print(f"✗ {seq_name:45s} → ERRO: {e}")

conn.commit()
cur.close()
conn.close()

print()
print("=" * 70)
print("✅ Sequences atualizadas com sucesso!")
print("=" * 70)
