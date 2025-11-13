#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug: Inspecionar HTML da página de dados históricos do CoinGecko
"""

import requests
from bs4 import BeautifulSoup
import sys
from pathlib import Path

# Adicionar root ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from services.coingecko_scraper import get_realistic_headers

def inspect_coingecko_page(coin_id: str):
    """Analisa estrutura HTML da página de dados históricos."""
    
    url = f"https://www.coingecko.com/en/coins/{coin_id}/historical_data"
    print(f"🔍 A analisar: {url}\n")
    
    session = requests.Session()
    headers = get_realistic_headers()
    
    # Visitar homepage primeiro
    print("1. A visitar homepage...")
    session.get("https://www.coingecko.com/", headers=headers, timeout=15)
    
    # Aceder à página de dados históricos
    print("2. A aceder à página de dados históricos...")
    resp = session.get(url, headers=headers, timeout=15)
    print(f"   Status: {resp.status_code}")
    print(f"   Content-Type: {resp.headers.get('Content-Type')}\n")
    
    # Parse HTML
    soup = BeautifulSoup(resp.content, "html.parser")
    
    # Procurar todos os links
    print("3. Links encontrados com 'export', 'download', 'csv', 'data':")
    print("-" * 80)
    
    found_any = False
    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        text = link.get_text(strip=True)
        
        keywords = ["export", "download", "csv", "data", "historical"]
        if any(kw in href.lower() or kw in text.lower() for kw in keywords):
            print(f"   Text: {text[:60]}")
            print(f"   Href: {href[:100]}")
            print(f"   Classes: {link.get('class', [])}")
            print()
            found_any = True
    
    if not found_any:
        print("   ❌ Nenhum link relevante encontrado!")
        print("\n4. A procurar botões com data-* attributes:")
        print("-" * 80)
        
        for btn in soup.find_all(["button", "a"]):
            attrs = btn.attrs
            has_data_attr = any(k.startswith("data-") for k in attrs.keys())
            if has_data_attr:
                print(f"   Tag: {btn.name}")
                print(f"   Text: {btn.get_text(strip=True)[:60]}")
                print(f"   Attributes: {attrs}")
                print()
    
    # Procurar scripts que possam conter URLs
    print("\n5. Scripts que mencionam 'csv' ou 'export':")
    print("-" * 80)
    
    for script in soup.find_all("script"):
        script_text = script.get_text()
        if "csv" in script_text.lower() or "export" in script_text.lower():
            # Mostrar trecho relevante
            lines = script_text.split("\n")
            for i, line in enumerate(lines):
                if "csv" in line.lower() or "export" in line.lower():
                    print(f"   Linha {i}: {line.strip()[:100]}")
                    if i > 0:
                        print(f"   Contexto: {lines[i-1].strip()[:80]}")
                    break
            print()
    
    print("\n6. Estrutura geral da página:")
    print("-" * 80)
    print(f"   Title: {soup.title.string if soup.title else 'N/A'}")
    print(f"   Total links: {len(soup.find_all('a'))}")
    print(f"   Total buttons: {len(soup.find_all('button'))}")
    print(f"   Total scripts: {len(soup.find_all('script'))}")
    
    # Guardar HTML para inspeção manual
    with open("debug_coingecko_page.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
    print(f"\n✅ HTML guardado em: debug_coingecko_page.html")

if __name__ == "__main__":
    coin = "bitcoin"
    if len(sys.argv) > 1:
        coin = sys.argv[1]
    
    inspect_coingecko_page(coin)
