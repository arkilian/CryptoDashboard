"""Serviço para gestão de snapshots de preços históricos.

Este módulo permite:
- Buscar preços históricos do CoinGecko e armazená-los localmente
- Consultar preços históricos da base de dados
- Preencher gaps de dados históricos
- Atualizar preços diários automaticamente
"""
import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
from sqlalchemy import text
from database.connection import get_engine
from services.coingecko import CoinGeckoService
import time

logger = logging.getLogger(__name__)

# URL base da API CoinGecko
BASE_URL = "https://api.coingecko.com/api/v3"

# Cache global para evitar chamadas repetidas durante mesma execução
_prices_session_cache = {}  # {(symbol, date): price}


def get_historical_price(asset_id: int, target_date: date) -> Optional[float]:
    """Busca o preço de um ativo numa data específica.
    
    Primeiro tenta na BD local, depois no CoinGecko se não encontrar.
    
    Args:
        asset_id: ID do ativo na tabela t_assets
        target_date: Data para a qual queremos o preço
        
    Returns:
        Preço em EUR ou None se não disponível
    """
    engine = get_engine()
    
    # Tentar buscar da BD
    df = pd.read_sql(
        """
        SELECT price_eur 
        FROM t_price_snapshots 
        WHERE asset_id = %s AND snapshot_date = %s
        LIMIT 1
        """,
        engine,
        params=(asset_id, target_date)
    )
    
    if not df.empty:
        return float(df.iloc[0]['price_eur'])
    
    # Se não encontrar, buscar do CoinGecko e guardar
    logger.info(f"Preço não encontrado localmente para asset_id={asset_id} em {target_date}. Buscando do CoinGecko...")
    
    # Buscar symbol e coingecko_id
    df_asset = pd.read_sql(
        "SELECT symbol, coingecko_id FROM t_assets WHERE asset_id = %s",
        engine,
        params=(asset_id,)
    )
    
    if df_asset.empty or not df_asset.iloc[0]['coingecko_id']:
        logger.warning(f"Asset {asset_id} não tem coingecko_id configurado")
        return None
    
    coingecko_id = df_asset.iloc[0]['coingecko_id']
    
    # Buscar preço histórico do CoinGecko usando endpoint de histórico por data específica
    try:
        import requests
        import time
        
        # DELAY: Adicionar pausa para respeitar rate limit do CoinGecko (10-30 req/min na API gratuita)
        # Reduced from 2s to 0.5s - still respectful but 4x faster (allows ~30 req/min)
        time.sleep(0.5)
        
        days_ago = (date.today() - target_date).days
        
        if days_ago < 0:
            logger.warning(f"Data futura solicitada: {target_date}")
            return None
        
        # Para hoje, usar endpoint de preço atual
        if days_ago == 0:
            url = f"{BASE_URL}/simple/price"
            params = {"ids": coingecko_id, "vs_currencies": "eur"}
            
            resp = requests.get(url, params=params, timeout=10)
            if resp.ok:
                data = resp.json()
                price = data.get(coingecko_id, {}).get("eur")
                if price:
                    closest_price = float(price)
                else:
                    logger.warning(f"Preço atual não disponível para {coingecko_id}")
                    return None
            else:
                logger.warning(f"Erro ao buscar preço atual: {resp.status_code}")
                return None
        else:
            # Para datas históricas, usar endpoint /coins/{id}/history
            # Formato da data: DD-MM-YYYY
            date_str = target_date.strftime("%d-%m-%Y")
            url = f"{BASE_URL}/coins/{coingecko_id}/history"
            params = {"date": date_str, "localization": "false"}
            
            resp = requests.get(url, params=params, timeout=15)
            if resp.ok:
                data = resp.json()
                # market_data contém os preços por moeda
                market_data = data.get("market_data", {})
                current_price = market_data.get("current_price", {})
                price = current_price.get("eur")
                
                if price:
                    closest_price = float(price)
                else:
                    logger.warning(f"Preço histórico não disponível para {coingecko_id} em {date_str}")
                    return None
            else:
                logger.warning(f"Erro ao buscar preço histórico: {resp.status_code}")
                return None
        
        if closest_price:
            # Guardar na BD para uso futuro
            try:
                with engine.begin() as conn:
                    conn.execute(
                        text("""
                            INSERT INTO t_price_snapshots (asset_id, snapshot_date, price_eur, source)
                            VALUES (:asset_id, :snapshot_date, :price_eur, 'coingecko')
                            ON CONFLICT (asset_id, snapshot_date) 
                            DO UPDATE SET price_eur = EXCLUDED.price_eur, source = EXCLUDED.source
                        """),
                        {
                            'asset_id': asset_id,
                            'snapshot_date': target_date,
                            'price_eur': closest_price,
                        }
                    )
                logger.info(f"Preço histórico guardado: asset_id={asset_id}, date={target_date}, price={closest_price}")
            except Exception as e:
                logger.error(f"Erro ao guardar snapshot: {e}")
            
            return float(closest_price)
        
    except Exception as e:
        logger.error(f"Erro ao buscar preço histórico do CoinGecko: {e}")
    
    return None


def get_historical_prices_bulk(asset_ids: List[int], target_date: date) -> Dict[int, float]:
    """Busca preços históricos para múltiplos ativos numa data.
    
    Args:
        asset_ids: Lista de IDs de ativos
        target_date: Data para a qual queremos os preços
        
    Returns:
        Dicionário {asset_id: price_eur}
    """
    if not asset_ids:
        return {}
    
    engine = get_engine()
    
    # Buscar da BD em batch PRIMEIRO
    placeholders = ','.join(['%s'] * len(asset_ids))
    df = pd.read_sql(
        f"""
        SELECT asset_id, price_eur 
        FROM t_price_snapshots 
        WHERE asset_id IN ({placeholders}) AND snapshot_date = %s
        """,
        engine,
        params=(*asset_ids, target_date)
    )
    
    # Convert to dictionary efficiently using pandas to_dict
    result = dict(zip(df['asset_id'].astype(int), df['price_eur'].astype(float)))
    
    if result:
        logger.info(f"✅ Encontrados {len(result)}/{len(asset_ids)} preços na BD para {target_date}")
    
    # Para assets sem preço na BD, buscar com rate limiting otimizado
    missing = [aid for aid in asset_ids if aid not in result]
    if missing:
        logger.info(f"🌐 Buscando {len(missing)} preços em falta do CoinGecko para {target_date}...")
        
        # Note: get_historical_price already includes 0.5s sleep
        # No additional sleep needed here to avoid double rate limiting
        for aid in missing:
            price = get_historical_price(aid, target_date)  # Busca CoinGecko e guarda na BD
            if price:
                result[aid] = price
    
    return result


def get_historical_prices_by_symbol(symbols: List[str], target_date: date) -> Dict[str, float]:
    """Busca preços históricos para múltiplos símbolos numa data.
    
    Args:
        symbols: Lista de símbolos de ativos (ex: ['BTC', 'ADA', 'ETH'])
        target_date: Data para a qual queremos os preços
        
    Returns:
        Dicionário {symbol: price_eur}
    """
    if not symbols:
        return {}
    
    # Verificar cache de sessão primeiro
    result = {}
    missing_symbols = []
    
    for sym in symbols:
        cache_key = (sym, target_date)
        if cache_key in _prices_session_cache:
            result[sym] = _prices_session_cache[cache_key]
        else:
            missing_symbols.append(sym)
    
    if not missing_symbols:
        return result  # Todos no cache
    
    engine = get_engine()
    
    # Buscar asset_ids dos símbolos
    placeholders = ','.join(['%s'] * len(missing_symbols))
    df_assets = pd.read_sql(
        f"""
        SELECT asset_id, symbol 
        FROM t_assets 
        WHERE symbol IN ({placeholders})
        """,
        engine,
        params=tuple(missing_symbols)
    )
    
    if df_assets.empty:
        return result
    
    # Mapear symbol -> asset_id efficiently using pandas to_dict
    symbol_to_id = dict(zip(df_assets['symbol'], df_assets['asset_id'].astype(int)))
    asset_ids = list(symbol_to_id.values())
    
    # Buscar preços históricos por asset_id (com rate limiting)
    prices_by_id = get_historical_prices_bulk(asset_ids, target_date)
    
    # Mapear de volta para símbolos e guardar no cache
    for symbol, asset_id in symbol_to_id.items():
        if asset_id in prices_by_id:
            price = prices_by_id[asset_id]
            result[symbol] = price
            _prices_session_cache[(symbol, target_date)] = price
    
    return result


def populate_snapshots_for_period(start_date: date, end_date: date, asset_ids: Optional[List[int]] = None):
    """Preenche snapshots de preços para um período.
    
    Args:
        start_date: Data inicial
        end_date: Data final
        asset_ids: Lista de asset_ids (se None, usa todos os ativos com coingecko_id)
    """
    engine = get_engine()
    
    if asset_ids is None:
        df_assets = pd.read_sql(
            "SELECT asset_id FROM t_assets WHERE coingecko_id IS NOT NULL",
            engine
        )
        asset_ids = df_assets['asset_id'].tolist()
    
    if not asset_ids:
        logger.warning("Nenhum ativo com coingecko_id configurado")
        return
    
    logger.info(f"Preenchendo snapshots de {start_date} a {end_date} para {len(asset_ids)} ativos")
    
    # Iterar por cada dia
    current = start_date
    while current <= end_date:
        logger.info(f"Processando {current}...")
        for asset_id in asset_ids:
            get_historical_price(asset_id, current)
        current += timedelta(days=1)
    
    logger.info("Preenchimento de snapshots concluído")


def update_latest_prices():
    """Atualiza os preços de hoje para todos os ativos configurados."""
    today = date.today()
    populate_snapshots_for_period(today, today)


if __name__ == "__main__":
    # Teste manual
    logging.basicConfig(level=logging.INFO)
    
    # Exemplo: buscar preço do BTC em 2024-01-01
    # price = get_historical_price(1, date(2024, 1, 1))
    # print(f"BTC em 2024-01-01: €{price}")
    
    # Atualizar preços de hoje
    update_latest_prices()
