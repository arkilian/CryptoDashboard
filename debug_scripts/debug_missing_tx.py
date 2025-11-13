"""Debug: Buscar a transação específica que está a faltar e tentar inserir manualmente."""
from services.cardano_api import CardanoScanAPI
from database.api_config import get_active_apis
from database.connection import get_connection, return_connection
import json
from datetime import datetime, timezone

# Get API
apis = get_active_apis()
api = CardanoScanAPI(apis[0]['api_key'])

address = "addr1q86l9qs02uhmh95yj8vgmecky4yfkxlctaae8axx0xut63p42ytjhzpls30rpmffa6y335yrxcuzh0q55d30ramjyefqvyf4rw"

print("🔍 Buscando transações (2 páginas)...")
transactions, error = api.get_transactions(address, max_pages=2)

if error:
    print(f"❌ Erro: {error}")
    exit(1)

print(f"✅ Encontradas {len(transactions)} transações")

# Procurar a transação que falta
target_hash = "2cf89fd74718ce9d"
target_tx = None

for tx in transactions:
    if tx.get('hash', '').startswith(target_hash):
        target_tx = tx
        break

if not target_tx:
    print(f"\n❌ Transação {target_hash}... NÃO encontrada na API!")
    print("\nPrimeiras 5 transações retornadas:")
    for i, tx in enumerate(transactions[:5], 1):
        print(f"  {i}. {tx.get('hash', 'N/A')[:16]}... | {tx.get('timestamp', 'N/A')}")
else:
    print(f"\n✅ Transação {target_hash}... ENCONTRADA!")
    print(f"\nDados completos:")
    print(json.dumps(target_tx, indent=2, default=str))
    
    # Tentar ver se ela já existe na BD
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT tx_hash, tx_timestamp, status FROM t_cardano_transactions WHERE tx_hash = %s", (target_tx['hash'],))
    existing = cur.fetchone()
    
    if existing:
        print(f"\n⚠️ Transação JÁ EXISTE na BD:")
        print(f"   Hash: {existing[0]}")
        print(f"   Timestamp: {existing[1]}")
        print(f"   Status: {existing[2]}")
    else:
        print(f"\n❌ Transação NÃO existe na BD")
        
        # Tentar inserir manualmente
        print("\n🔧 Tentando inserir manualmente...")
        
        ts = target_tx.get("timestamp")
        if isinstance(ts, str) and "T" in ts:
            tx_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        else:
            tx_dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        
        fees_ada = 0.0
        try:
            fees_ada = float(target_tx.get("fees", 0))
        except:
            pass
        
        try:
            cur.execute(
                """
                INSERT INTO t_cardano_transactions (tx_hash, wallet_id, address, block_height, tx_timestamp, status, fees_ada, raw_payload)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tx_hash) DO NOTHING
                """,
                (
                    target_tx['hash'],
                    2,  # wallet_id
                    address,
                    target_tx.get("block_height") or target_tx.get("blockHeight"),
                    tx_dt,
                    "confirmed",
                    fees_ada,
                    json.dumps(target_tx),
                )
            )
            conn.commit()
            
            if cur.rowcount > 0:
                print(f"✅ Transação inserida com sucesso!")
            else:
                print(f"⚠️ INSERT retornou 0 rows (já existia ou conflito)")
            
        except Exception as e:
            print(f"❌ Erro ao inserir: {e}")
            conn.rollback()
    
    return_connection(conn)
