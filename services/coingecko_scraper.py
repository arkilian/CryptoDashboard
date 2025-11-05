#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CoinGecko Historical Data Scraper
----------------------------------
Web scraper para fazer download de dados históricos do CoinGecko e popular t_price_snapshots.

Funcionalidades:
- Download automático de CSV de dados históricos do CoinGecko
- Parsing de CSV e conversão EUR via taxa USD->EUR histórica
- Bulk insert na base de dados (t_price_snapshots)
- Suporte a múltiplas moedas configuráveis

Uso:
    python -m services.coingecko_scraper --coin cardano --days 365
    python -m services.coingecko_scraper --coin bitcoin --all
    python -m services.coingecko_scraper --coin cardano --csv cardano/ada-usd-max.csv --all
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
    "djed": "DJED",
    "usd-coin": "USDC",
    "tether": "USDT",
}

# Headers para simular browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
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
    # Taxa fixa: simplifica e evita rate limits
    if use_fixed_rate:
        return 0.92
    
    # Cache hit
    if target_date in _usd_eur_cache:
        return _usd_eur_cache[target_date]
    
    """
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


def download_coingecko_csv(coin_id: str, cache_dir: str = "cache") -> Optional[str]:
    """
    Faz download do CSV de dados históricos do CoinGecko via web scraping.
    
    Args:
        coin_id: ID da moeda no CoinGecko (ex: 'cardano', 'bitcoin')
        cache_dir: Diretório para guardar CSV (opcional)
        
    Returns:
        Path do ficheiro CSV ou None se falhar
    """
    # URL da página de dados históricos
    historical_url = f"https://www.coingecko.com/en/coins/{coin_id}/historical_data"
    
    logger.info(f"🌐 A aceder à página: {historical_url}")
    
    try:
        # Aceder à página de dados históricos
        session = requests.Session()
        resp = session.get(historical_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        
        # Parse HTML para encontrar link de download CSV
        soup = BeautifulSoup(resp.content, "html.parser")
        
        # Procurar botão/link de download CSV
        # Nota: a estrutura HTML pode mudar, tentamos várias abordagens
        csv_link = None
        
        # Tentativa 1: Link direto com 'download' ou 'csv' no href
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if "csv" in href.lower() or "download" in href.lower():
                if coin_id in href:
                    csv_link = href
                    break
        
        # Tentativa 2: Botão com data-* attributes (comum em SPAs)
        if not csv_link:
            for btn in soup.find_all(["button", "a"], attrs={"data-export": True}):
                csv_link = btn.get("data-url") or btn.get("href")
                if csv_link:
                    break
        
        # Tentativa 3: Construir URL manualmente (padrão conhecido)
        if not csv_link:
            # Formato típico: /coins/[coin_id]/historical_data/usd?download=true
            csv_link = f"/en/coins/{coin_id}/historical_data/usd"
            logger.info(f"⚠️ Link CSV não encontrado no HTML, a tentar URL padrão")
        
        # Construir URL absoluta
        if csv_link.startswith("/"):
            csv_link = urljoin("https://www.coingecko.com", csv_link)
        elif not csv_link.startswith("http"):
            csv_link = urljoin(historical_url, csv_link)
        
        logger.info(f"📥 A fazer download do CSV: {csv_link}")
        
        # Download do CSV
        csv_params = {"download": "true"} if "download" not in csv_link else {}
        csv_resp = session.get(csv_link, headers=HEADERS, params=csv_params, timeout=30)
        csv_resp.raise_for_status()
        
        # Verificar se recebemos CSV
        content_type = csv_resp.headers.get("Content-Type", "")
        if "csv" not in content_type.lower() and "text/plain" not in content_type.lower():
            # Pode ser HTML com erro - tentar parsing direto
            if csv_resp.text.startswith("<!DOCTYPE") or "<html" in csv_resp.text[:100]:
                logger.error("❌ Resposta é HTML, não CSV. O scraping pode ter falhado.")
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
        return None
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}")
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
            return 0
        asset_id = row[0]
        coingecko_id = row[1]
    
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
        
    Returns:
        Número de registos inseridos
    """
    # Auto-detect symbol
    if not asset_symbol:
        asset_symbol = COIN_MAPPING.get(coin_id.lower())
        if not asset_symbol:
            logger.error(f"❌ Moeda '{coin_id}' não mapeada. Use --symbol para especificar.")
            return 0
    
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
        csv_path = download_coingecko_csv(coin_id)
        if not csv_path:
            logger.error("❌ Falha no download do CSV")
            return 0
    
    # Parse e inserir
    count = parse_csv_and_insert(csv_path, asset_symbol, limit_days, skip_existing, use_fixed_rate)
    
    return count


def main():
    """CLI interface."""
    parser = argparse.ArgumentParser(description="CoinGecko Historical Data Scraper")
    parser.add_argument("--coin", required=True, help="CoinGecko coin ID (ex: cardano, bitcoin)")
    parser.add_argument("--symbol", help="Asset symbol na BD (auto-detect se omitido)")
    parser.add_argument("--csv", help="Path para CSV existente (skip download)")
    parser.add_argument("--days", type=int, help="Limitar aos N dias mais recentes")
    parser.add_argument("--all", action="store_true", help="Processar todos os dados históricos")
    parser.add_argument("--overwrite", action="store_true", help="Sobrescrever dados existentes")
    parser.add_argument("--dynamic-rate", action="store_true", help="Usar taxa USD->EUR dinâmica (lento, pode ter timeouts)")
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
    )
    
    if count > 0:
        print(f"\n✅ Sucesso! {count} registos inseridos em t_price_snapshots")
    else:
        print(f"\n❌ Nenhum registo foi inserido")


if __name__ == "__main__":
    main()
