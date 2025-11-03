import requests
import json
from pycardano import Address

API_KEY = "771d0a8a-9978-40b4-b60b-3fa873e5209d"
ADDRESS_BECH32 = "addr1q86l9qs02uhmh95yj8vgmecky4yfkxlctaae8axx0xut63p42ytjhzpls30rpmffa6y335yrxcuzh0q55d30ramjyefqvyf4rw"
OUTPUT_FILE = "balance.json"

HEADERS = {"apiKey": API_KEY}

# --- usa query param (conforme docs) ---
BASE_URL = "https://api.cardanoscan.io/api/v1/address/balance"
params = {"address": ADDRESS_BECH32}

print(f"🔎 A obter saldo do endereço:\n{ADDRESS_BECH32}\n")

resp = requests.get(BASE_URL, headers=HEADERS, params=params)

if resp.status_code == 404:
    # Mensagem clara para o utilizador: API não encontrou registos
    print("❌ Erro 404: Endereço não encontrado pela API.")
    print("   Possíveis causas:")
    print("   - Endereço nunca foi usado on-chain (a API não indexou nada).")
    print("   - Indexação atrasada / endpoint temporariamente indisponível.")
    print("   - Formato do endereço incorreto (deve ser bech32).")
    print("\n   Recomendação: confirma que o endereço já fez pelo menos uma transação on-chain")
    print("   (p.ex. procura no cardanoscan.io) — se existir transação, tenta novamente.")
    # grava o body para análise
    try:
        print("\nResposta da API:", resp.json())
    except Exception:
        print("\nResposta da API (raw):", resp.text)
    exit(1)

if resp.status_code != 200:
    print(f"❌ Erro ao obter saldo ({resp.status_code}): {resp.text}")
    exit(1)

data = resp.json()

# grava resposta completa
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

# Extrai e mostra saldo ADA
lovelace = int(data.get("balance", 0))
ada = lovelace / 1_000_000
print(f"💰 Saldo ADA: {lovelace:,} lovelace ({ada:.6f} ADA)".replace(",", "."))

# Lista tokens nativos (se existirem)
tokens = data.get("tokens") or data.get("assets") or []
if tokens:
    print("\n🔹 Tokens / Assets encontrados:")
    for t in tokens:
        # as chaves podem variar conforme o endpoint / versão; tentamos várias
        name = t.get("name") or t.get("assetName") or t.get("policyId", "")[:12]
        qty = int(t.get("quantity", t.get("amount", 0)))
        policy = t.get("policyId") or t.get("policy", "") 
        print(f"  - {name} (policy {policy[:12]}...): {qty:,}".replace(",", "."))
else:
    print("\n⚪ Nenhum token nativo encontrado.")

print(f"\n💾 Resposta completa escrita em: {OUTPUT_FILE}")
