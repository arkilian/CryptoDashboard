"""Sincronizar wallet 2 (Vespr) para pegar transação em falta."""
from services.cardano_sync import sync_wallet_transactions

address = "addr1q86l9qs02uhmh95yj8vgmecky4yfkxlctaae8axx0xut63p42ytjhzpls30rpmffa6y335yrxcuzh0q55d30ramjyefqvyf4rw"
wallet_id = 2

print(f"🔄 Sincronizando wallet {wallet_id} (20 páginas)...")
print(f"   Endereço: {address[:30]}...")

try:
    tx_count, io_total = sync_wallet_transactions(wallet_id, address, max_pages=20)
    print(f"\n✅ Sincronização concluída!")
    print(f"   - {tx_count} transações processadas")
    print(f"   - {io_total} linhas IO no total")
except Exception as e:
    print(f"\n❌ Erro: {e}")
