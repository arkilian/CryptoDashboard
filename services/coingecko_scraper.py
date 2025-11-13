#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CoinGecko Historical Data Scraper
----------------------------------
Parser de CSV para importar dados históricos do CoinGecko em t_price_snapshots.

⚠️ IMPORTANTE: Web scraping automático NÃO FUNCIONA
O CoinGecko bloqueia acesso automático ao CSV com 403 Forbidden, mesmo com:
- Headers realistas (Chrome 131, sec-ch-ua, referer)
- Navegação sequencial (homepage → página → download)
- Session persistente com cookies
- Selenium WebDriver

Motivo: Página é SPA (JavaScript dinâmico) + proteções Cloudflare/anti-bot.

✅ SOLUÇÃO RECOMENDADA: Download manual do CSV
1. Aceder: https://www.coingecko.com/en/coins/cardano/historical_data
2. Clicar: "Export Data" → "Download CSV"
3. Guardar: cardano/ada-usd-max.csv
4. Importar: python -m services.coingecko_scraper --coin cardano --csv cardano/ada-usd-max.csv --all

Funcionalidades:
- ✅ Parse de CSV do CoinGecko (formato: snapped_at, price, market_cap, total_volume)
- ✅ Conversão USD→EUR (taxa fixa 0.92 ou dinâmica via API)
- ✅ Bulk insert em t_price_snapshots (batching 1000 registos)
- ✅ ON CONFLICT handling (skip ou overwrite)
- ⚠️ Web scraping (experimental, geralmente bloqueado)

Uso:
    # RECOMENDADO: CSV manual
    python -m services.coingecko_scraper --coin cardano --csv cardano/ada-usd-max.csv --all
    
    # Experimental: tentar scraping automático (geralmente falha)
    python -m services.coingecko_scraper --coin bitcoin --days 30
    
    # Fallback: Selenium (requer pip install selenium)
    python -m services.coingecko_scraper --coin ethereum --selenium --all
"""

import argparse
import csv
import logging
import os
import time
from datetime import datetime, date
from io import StringIO
from typing import Optional, Dict, List, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from sqlalchemy import text

from database.connection import get_engine

logger = logging.getLogger(__name__)

# Mapeamento de coins CoinGecko -> asset symbol na BD
COIN_MAPPING = {
    "cardano": "ADA",
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "sui": "SUI",
    "djed": "DJED",
    "shen": "SHEN",
    "usd-coin": "USDC",
    "tether": "USDT",
}

# Headers melhorados para simular browser real (anti-bot)
def get_realistic_headers() -> Dict[str, str]:
    """
    Retorna headers realistas que imitam um browser Chrome recente.
    Inclui headers adicionais que sites anti-bot verificam.
    """
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,pt;q=0.8",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "cache-control": "max-age=0",
        "DNT": "1",
        "Connection": "keep-alive",
        # Referer simulado (como se viesse da homepage)
        "Referer": "https://www.coingecko.com/",
    }


# Cache de taxas USD->EUR para evitar chamadas repetidas
_usd_eur_cache: Dict[date, float] = {}

def get_usd_to_eur_rate(target_date: date, use_fixed_rate: bool = True) -> float:
    """
    Obtém taxa de conversão USD->EUR para uma data específica.
    
    Estratégia simplificada: usa taxa fixa 0.92 (média histórica 2017-2025)
    para evitar rate limits e timeouts.
    
    Args:
        target_date: Data para a qual queremos a taxa
        use_fixed_rate: Se True, usa taxa fixa (recomendado)
        
    Returns:
        Taxa de conversão USD->EUR
    """
    # Taxa fixa: simplifica e evita rate limits
    if use_fixed_rate:
        return 0.92
    
    # Cache hit
    if target_date in _usd_eur_cache:
        return _usd_eur_cache[target_date]
    
    try:
        # ECB API endpoint (apenas se use_fixed_rate=False)
        url = f"https://api.exchangerate.host/{target_date.strftime('%Y-%m-%d')}"
        params = {"base": "USD", "symbols": "EUR"}
        
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            rate = data.get("rates", {}).get("EUR")
            if rate:
                _usd_eur_cache[target_date] = float(rate)
                return float(rate)
    except Exception as e:
        logger.debug(f"Erro ao obter taxa USD->EUR para {target_date}: {e}")
    
    # Fallback: taxa média histórica
    _usd_eur_cache[target_date] = 0.92
    return 0.92


def download_coingecko_csv(coin_id: str, cache_dir: str = "cache", use_selenium: bool = False) -> Optional[str]:
    """
    Faz download do CSV de dados históricos do CoinGecko via web scraping.
    ⚠️ AVISO: Esta função geralmente FALHA com 403 Forbidden
    O CoinGecko protege o endpoint de download mesmo com headers realistas.
    
    Comportamento observado (2025-11-05):
    - ✅ Homepage carrega (200 OK)
    - ✅ Página da moeda carrega (200 OK)  
    - ❌ Endpoint CSV retorna 403 Forbidden
    - ❌ HTML é SPA (JavaScript dinâmico, 0 links parseáveis)
    
    RECOMENDAÇÃO: Usar --csv com arquivo baixado manualmente do site.
    Ver: docs/COINGECKO_CSV_IMPORT.md
    
    
    Estratégias anti-bloqueio:
    1. Headers realistas (Chrome 131, sec-ch-ua, referer)
    2. Session persistente (mantém cookies)
    3. Delay entre requests (1-2s)
    4. Opção Selenium para casos difíceis
    
    Args:
        coin_id: ID da moeda no CoinGecko (ex: 'cardano', 'bitcoin')
        cache_dir: Diretório para guardar CSV (opcional)
        use_selenium: Usar Selenium WebDriver (mais lento, mas bypassa JS anti-bot)
        
    Returns:
        Path do ficheiro CSV ou None se falhar
    """
    # URL da página de dados históricos
    historical_url = f"https://www.coingecko.com/en/coins/{coin_id}/historical_data"
    
    logger.info(f"🌐 A aceder à página: {historical_url}")
    
    if use_selenium:
        return _download_with_selenium(coin_id, historical_url, cache_dir)
    
    try:
        # Session persistente (mantém cookies entre requests)
        session = requests.Session()
        headers = get_realistic_headers()
        
        # Passo 1: Visitar homepage primeiro (simular navegação real)
        logger.info("🏠 A visitar homepage do CoinGecko...")
        session.get("https://www.coingecko.com/", headers=headers, timeout=15)
        time.sleep(1.5)  # Delay natural
        
        # Passo 2: Aceder à página de dados históricos
        logger.info(f"📄 A aceder à página da moeda...")
        resp = session.get(historical_url, headers=headers, timeout=15)
        resp.raise_for_status()
        
        time.sleep(1.0)  # Delay antes do download
        
        # Parse HTML para encontrar link de download CSV
        soup = BeautifulSoup(resp.content, "html.parser")
        
        # Procurar botão/link de download CSV
        csv_link = None
        
        # Tentativa 1: Link direto com 'download' ou 'csv' no href
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if "csv" in href.lower() or "download" in href.lower():
                if coin_id in href or "historical_data" in href:
                    csv_link = href
                    logger.info(f"✓ Link CSV encontrado: {href[:80]}...")
                    break
        
        # Tentativa 2: Botão com data-* attributes (comum em SPAs)
        if not csv_link:
            for btn in soup.find_all(["button", "a"], attrs={"data-export": True}):
                csv_link = btn.get("data-url") or btn.get("href")
                if csv_link:
                    logger.info(f"✓ Link via data-export: {csv_link[:80]}...")
                    break
        
        # Tentativa 3: Procurar por padrão "Export" no texto
        if not csv_link:
            for link in soup.find_all("a", text=lambda t: t and "export" in t.lower()):
                csv_link = link.get("href")
                if csv_link:
                    logger.info(f"✓ Link via texto 'Export': {csv_link[:80]}...")
                    break
        
        # Tentativa 4: Construir URL manualmente (padrão conhecido)
        if not csv_link:
            csv_link = f"/en/coins/{coin_id}/historical_data/usd"
            logger.warning(f"⚠️ Link CSV não encontrado no HTML, a tentar URL padrão")
        
        # Construir URL absoluta
        if csv_link.startswith("/"):
            csv_link = urljoin("https://www.coingecko.com", csv_link)
        elif not csv_link.startswith("http"):
            csv_link = urljoin(historical_url, csv_link)
        
        logger.info(f"📥 A fazer download do CSV: {csv_link}")
        
        # Atualizar headers com referer da página de dados históricos
        headers["Referer"] = historical_url
        headers["sec-fetch-site"] = "same-origin"
        
        # Download do CSV com parâmetros adicionais
        csv_params = {"download": "true"} if "?" not in csv_link else {}
        csv_resp = session.get(csv_link, headers=headers, params=csv_params, timeout=30)
        csv_resp.raise_for_status()
        
        # Verificar se recebemos CSV
        content_type = csv_resp.headers.get("Content-Type", "")
        if "csv" not in content_type.lower() and "text/plain" not in content_type.lower():
            # Pode ser HTML com erro - tentar parsing direto
            if csv_resp.text.startswith("<!DOCTYPE") or "<html" in csv_resp.text[:100]:
                logger.error("❌ Resposta é HTML, não CSV. O scraping foi bloqueado.")
                logger.info("💡 Tenta usar --selenium para bypass com WebDriver")
                return None
        
        # Guardar em cache
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, f"{coin_id}-usd-max.csv")
        
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(csv_resp.text)
        
        logger.info(f"✅ CSV guardado em: {cache_path}")
        return cache_path
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erro de rede ao fazer download: {e}")
        logger.info("💡 Possíveis soluções:")
        logger.info("   1. Usar --selenium para bypass com WebDriver")
        logger.info("   2. Descarregar CSV manualmente e usar --csv <path>")
        logger.info("   3. Tentar novamente mais tarde (rate limit temporário)")
        return None
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}")
        return None


def _download_with_selenium(coin_id: str, url: str, cache_dir: str) -> Optional[str]:
    """
    Fallback usando Selenium WebDriver para bypass de proteções JS.
    
    Requer: pip install selenium
    Opcional: chromedriver no PATH ou webdriver-manager
    
    Args:
        coin_id: ID da moeda
        url: URL da página de dados históricos
        cache_dir: Diretório para guardar CSV
        
    Returns:
        Path do CSV ou None
    """
    try:
        from selenium import webdriver  # type: ignore[import-unresolved]
        from selenium.webdriver.chrome.options import Options  # type: ignore[import-unresolved]
        from selenium.webdriver.common.by import By  # type: ignore[import-unresolved]
        from selenium.webdriver.support.ui import WebDriverWait  # type: ignore[import-unresolved]
        from selenium.webdriver.support import expected_conditions as EC  # type: ignore[import-unresolved]
        
        logger.info("🤖 A usar Selenium WebDriver...")
        
        # Configurar Chrome headless
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        
        # Aceder à página
        driver.get(url)
        time.sleep(3)  # Aguardar carregamento JS
        
        # Procurar botão de export CSV
        try:
            wait = WebDriverWait(driver, 10)
            # Adaptar seletor conforme estrutura real do site
            export_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Export') or contains(@href, 'csv')]"))
            )
            csv_url = export_btn.get_attribute("href")
            
            # Download do CSV
            driver.get(csv_url)
            time.sleep(2)
            
            # Obter conteúdo
            csv_content = driver.page_source
            
            # Guardar
            os.makedirs(cache_dir, exist_ok=True)
            cache_path = os.path.join(cache_dir, f"{coin_id}-usd-max.csv")
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(csv_content)
            
            driver.quit()
            logger.info(f"✅ CSV obtido via Selenium: {cache_path}")
            return cache_path
            
        except Exception as e:
            driver.quit()
            logger.error(f"❌ Erro ao localizar botão de export: {e}")
            return None
            
    except ImportError:
        logger.error("❌ Selenium não está instalado. Instala com: pip install selenium")
        return None
    except Exception as e:
        logger.error(f"❌ Erro no Selenium: {e}")
        return None


def parse_csv_and_insert(
    csv_path: str,
    asset_symbol: str,
    limit_days: Optional[int] = None,
    skip_existing: bool = True,
    use_fixed_rate: bool = True,
) -> int:
    """
    Parse CSV do CoinGecko e insere dados em t_price_snapshots.
    
    Args:
        csv_path: Path do ficheiro CSV
        asset_symbol: Símbolo do ativo na BD (ex: 'ADA', 'BTC')
        limit_days: Limitar aos N dias mais recentes (None = todos)
        skip_existing: Se True, não sobrescreve snapshots existentes
        use_fixed_rate: Se True, usa taxa USD->EUR fixa (0.92)
        
    Returns:
        Número de registos inseridos
    """
    engine = get_engine()
    
    # Verificar se asset existe
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT asset_id, coingecko_id FROM t_assets WHERE symbol = :symbol"),
            {"symbol": asset_symbol}
        )
        row = result.fetchone()
        if not row:
            logger.error(f"❌ Asset '{asset_symbol}' não encontrado em t_assets")
            logger.error(f"💡 Solução: Insere o asset primeiro:")
            logger.error(f"   INSERT INTO t_assets (symbol, name, coingecko_id, is_stablecoin)")
            logger.error(f"   VALUES ('{asset_symbol}', 'Nome do Asset', 'coin-id', FALSE);")
            return 0
        asset_id = row[0]
    
    logger.info(f"📊 A processar CSV para {asset_symbol} (asset_id={asset_id})")
    
    # Parse CSV
    rows_to_insert = []
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                # Parse data
                snapped_at_str = row.get("snapped_at", "")
                # Formato: "2017-10-18 00:00:00 UTC"
                dt = datetime.strptime(snapped_at_str, "%Y-%m-%d %H:%M:%S %Z")
                snapshot_date = dt.date()
                
                # Parse preço USD
                price_usd = float(row.get("price", 0))
                if price_usd <= 0:
                    continue
                
                # Converter para EUR
                usd_to_eur = get_usd_to_eur_rate(snapshot_date, use_fixed_rate=use_fixed_rate)
                price_eur = price_usd * usd_to_eur
                
                rows_to_insert.append({
                    "asset_id": asset_id,
                    "snapshot_date": snapshot_date,
                    "price_eur": price_eur,
                    "source": "coingecko_csv",
                })
                
            except Exception as e:
                logger.warning(f"⚠️ Erro ao processar linha: {e}")
                continue
    
    if not rows_to_insert:
        logger.warning("⚠️ Nenhum dado válido encontrado no CSV")
        return 0
    
    # Ordenar por data (mais recentes primeiro) e limitar
    rows_to_insert.sort(key=lambda x: x["snapshot_date"], reverse=True)
    if limit_days:
        rows_to_insert = rows_to_insert[:limit_days]
    
    logger.info(f"📝 A inserir {len(rows_to_insert)} registos...")
    
    # Bulk insert com ON CONFLICT
    conflict_clause = "DO NOTHING" if skip_existing else "DO UPDATE SET price_eur = EXCLUDED.price_eur, source = EXCLUDED.source"
    
    inserted_count = 0
    batch_size = 1000
    
    with engine.begin() as conn:
        for i in range(0, len(rows_to_insert), batch_size):
            batch = rows_to_insert[i:i+batch_size]
            
            try:
                conn.execute(
                    text(f"""
                        INSERT INTO t_price_snapshots (asset_id, snapshot_date, price_eur, source)
                        VALUES (:asset_id, :snapshot_date, :price_eur, :source)
                        ON CONFLICT (asset_id, snapshot_date) {conflict_clause}
                    """),
                    batch
                )
                inserted_count += len(batch)
                
                if (i + batch_size) % 5000 == 0:
                    logger.info(f"   ... {inserted_count}/{len(rows_to_insert)} inseridos")
                    
            except Exception as e:
                logger.error(f"❌ Erro ao inserir batch: {e}")
                continue
    
    logger.info(f"✅ Total inserido: {inserted_count} registos")
    return inserted_count


def scrape_and_populate(
    coin_id: str,
    asset_symbol: Optional[str] = None,
    limit_days: Optional[int] = None,
    skip_existing: bool = True,
    csv_file: Optional[str] = None,
    use_fixed_rate: bool = True,
    use_selenium: bool = False,
) -> int:
    """
    Pipeline completo: download CSV + parse + insert.
    
    Args:
        coin_id: ID da moeda no CoinGecko (ex: 'cardano')
        asset_symbol: Símbolo na BD (auto-detect via COIN_MAPPING se None)
        limit_days: Limitar aos N dias mais recentes
        skip_existing: Não sobrescrever dados existentes
        csv_file: Path para CSV existente (se fornecido, skip download)
        use_fixed_rate: Se True, usa taxa USD->EUR fixa (0.92)
        use_selenium: Usar Selenium para bypass (requer pip install selenium)
        
    Returns:
        Número de registos inseridos
    """
    # Auto-detect symbol
    if not asset_symbol:
        asset_symbol = COIN_MAPPING.get(coin_id.lower())
        if not asset_symbol:
            # Tentar usar o coin_id em uppercase como fallback
            asset_symbol = coin_id.upper()
            logger.warning(f"⚠️ Moeda '{coin_id}' não está no COIN_MAPPING")
            logger.warning(f"💡 A tentar usar '{asset_symbol}' como symbol")
            logger.warning(f"💡 Se falhar, usa: --symbol SYMBOL_CORRETO")
    
    logger.info(f"🚀 A processar: {coin_id} -> {asset_symbol}")
    
    # Usar CSV existente ou fazer download
    if csv_file:
        if not os.path.exists(csv_file):
            logger.error(f"❌ Ficheiro não encontrado: {csv_file}")
            return 0
        logger.info(f"📂 A usar CSV existente: {csv_file}")
        csv_path = csv_file
    else:
        # Download CSV
        csv_path = download_coingecko_csv(coin_id, use_selenium=use_selenium)
        if not csv_path:
            logger.error("❌ Falha no download do CSV")
            return 0
    
    # Parse e inserir
    count = parse_csv_and_insert(csv_path, asset_symbol, limit_days, skip_existing, use_fixed_rate)
    
    return count


def main():
    """CLI interface."""
    parser = argparse.ArgumentParser(
        description="CoinGecko Historical Data Scraper",
        epilog="""
Exemplos:
  # Usar CSV existente (recomendado)
  python -m services.coingecko_scraper --coin cardano --csv cardano/ada-usd-max.csv --all
  
  # Tentar download automático
  python -m services.coingecko_scraper --coin bitcoin --all
  
  # Usar Selenium para bypass (requer: pip install selenium)
  python -m services.coingecko_scraper --coin ethereum --selenium --all
        """
    )
    parser.add_argument("--coin", required=True, help="CoinGecko coin ID (ex: cardano, bitcoin)")
    parser.add_argument("--symbol", help="Asset symbol na BD (auto-detect se omitido)")
    parser.add_argument("--csv", help="Path para CSV existente (skip download)")
    parser.add_argument("--days", type=int, help="Limitar aos N dias mais recentes")
    parser.add_argument("--all", action="store_true", help="Processar todos os dados históricos")
    parser.add_argument("--overwrite", action="store_true", help="Sobrescrever dados existentes")
    parser.add_argument("--dynamic-rate", action="store_true", help="Usar taxa USD->EUR dinâmica (lento, pode ter timeouts)")
    parser.add_argument("--selenium", action="store_true", help="Usar Selenium WebDriver para bypass (requer selenium instalado)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Logging verbose")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    # Executar scraping
    limit_days = None if args.all else args.days
    
    count = scrape_and_populate(
        coin_id=args.coin,
        asset_symbol=args.symbol,
        limit_days=limit_days,
        skip_existing=not args.overwrite,
        csv_file=args.csv,
        use_fixed_rate=not args.dynamic_rate,
        use_selenium=args.selenium,
    )
    
    if count > 0:
        print(f"\n✅ Sucesso! {count} registos inseridos em t_price_snapshots")
    else:
        print(f"\n❌ Nenhum registo foi inserido")


if __name__ == "__main__":
    main()
