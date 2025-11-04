"""Verificar transações no CardanoScan vs BD."""
from services.cardano_api import CardanoScanAPI
from database.api_config import get_active_apis
from database.connection import get_connection, return_connection

# Get API
apis = get_active_apis()
if not apis:
    print("❌ Nenhuma API ativa")
    exit(1)

api = CardanoScanAPI(apis[0]['api_key'])

# Wallet 2 address (Vespr)
address = "addr1q86l9qs02uhmh95yj8vgmecky4yfkxlctaae8axx0xut63p42ytjhzpls30rpmffa6y335yrxcuzh0q55d30ramjyefqvyf4rw"
print(f"🔍 Verificando wallet: {address[:20]}...")

conn = get_connection()
cur = conn.cursor()

# Fetch transactions (20 páginas)
print("\n📡 Buscando transações do CardanoScan (1 página)...")
transactions, error = api.get_transactions(address, max_pages=1)

if error:
    print(f"❌ Erro: {error}")
    return_connection(conn)
    exit(1)

print(f"✅ Encontradas {len(transactions)} transações na página 1")

# Comparar hashes
print("\n" + "=" * 70)
print("Transações no CardanoScan (página 1):")
print("=" * 70)
api_hashes = set()
for i, tx in enumerate(transactions[:30], 1):  # Mostrar até 30
    tx_hash = tx.get('hash', '')
    timestamp = tx.get('timestamp', '')
    api_hashes.add(tx_hash)
    
    # Check if exists in DB
    cur.execute("SELECT 1 FROM t_cardano_transactions WHERE tx_hash = %s", (tx_hash,))
    exists = cur.fetchone() is not None
    status = "✅ Na BD" if exists else "❌ FALTA"
    
    print(f"  {i:2}. {tx_hash[:16]}... | {timestamp} | {status}")

# Transações na BD
print("\n" + "=" * 70)
print("Transações na BD (wallet 2):")
print("=" * 70)
cur.execute("""
    SELECT tx_hash, tx_timestamp 
    FROM t_cardano_transactions 
    WHERE wallet_id = 2 
    ORDER BY tx_timestamp DESC
""")
db_hashes = set()
for i, row in enumerate(cur.fetchall(), 1):
    db_hashes.add(row[0])
    in_api = "✅" if row[0] in api_hashes else "⚠️ Não aparece na pág 1"
    print(f"  {i:2}. {row[0][:16]}... | {row[1]} | {in_api}")

# Diferenças
print("\n" + "=" * 70)
print("Análise:")
print("=" * 70)
missing_in_db = api_hashes - db_hashes
missing_in_api = db_hashes - api_hashes

print(f"  Total na API (página 1): {len(api_hashes)}")
print(f"  Total na BD (wallet 2):  {len(db_hashes)}")
print(f"  ❌ Faltam na BD: {len(missing_in_db)}")
if missing_in_db:
    for h in list(missing_in_db)[:5]:
        print(f"     - {h[:16]}...")
print(f"  ⚠️ Na BD mas não na pág 1 da API: {len(missing_in_api)}")

return_connection(conn)
