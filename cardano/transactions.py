import requests
import json
from pycardano import Address
from time import sleep

# --- CONFIGURAÇÕES ---
API_KEY = "771d0a8a-9978-40b4-b60b-3fa873e5209d"
ADDRESS_BECH32 = "addr1q86l9qs02uhmh95yj8vgmecky4yfkxlctaae8axx0xut63p42ytjhzpls30rpmffa6y335yrxcuzh0q55d30ramjyefqvyf4rw"
OUTPUT_FILE = "transactions_all.json"

# --- CONVERTER PARA HEXADECIMAL ---
address_obj = Address.from_primitive(ADDRESS_BECH32)
address_hex = address_obj.to_primitive().hex()
print(f"Endereço HEX: {address_hex}")

# --- CONFIGURAÇÕES DE API ---
BASE_URL = "https://api.cardanoscan.io/api/v1/transaction/list"
HEADERS = {"apiKey": API_KEY}

# --- CONSULTAR PRIMEIRA PÁGINA PARA OBTER 'count' ---
first_url = f"{BASE_URL}?address={address_hex}&pageNo=1"
response = requests.get(first_url, headers=HEADERS)

if response.status_code != 200:
    print(f"❌ Erro inicial ({response.status_code}): {response.text}")
    exit()

data = response.json()
total_pages = data.get("count", 1)
all_transactions = data.get("transactions", [])

print(f"\n🔎 Total de páginas encontradas: {total_pages}")
print(f"📥 Página 1 carregada com {len(data.get('transactions', []))} transações.")

# --- LOOP PARA AS DEMAIS PÁGINAS ---
for page in range(2, total_pages + 1):
    url = f"{BASE_URL}?address={address_hex}&pageNo={page}"
    print(f"📄 A carregar página {page}/{total_pages}...")
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        page_data = response.json().get("transactions", [])
        all_transactions.extend(page_data)
        print(f"✅ Página {page}: {len(page_data)} transações adicionadas.")
    else:
        print(f"⚠️ Erro na página {page}: {response.text}")

    # Evita sobrecarregar o servidor
    sleep(0.3)

# --- EXPORTAR TODAS AS TRANSAÇÕES ---
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(all_transactions, f, indent=4, ensure_ascii=False)

print(f"\n💾 Exportação concluída: {OUTPUT_FILE}")
print(f"📊 Total de transações exportadas: {len(all_transactions)}")
