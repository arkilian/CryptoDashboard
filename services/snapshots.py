"""Serviço para gestão de snapshots de preços históricos.

Este módulo permite:
- Buscar preços históricos do CoinGecko e armazená-los localmente
- Consultar preços históricos da base de dados
- Preencher gaps de dados históricos
- Atualizar preços diários automaticamente
"""
import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from sqlalchemy import text
from database.connection import get_engine
from services.coingecko import CoinGeckoService

logger = logging.getLogger(__name__)


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
    
    # Buscar preço histórico do CoinGecko usando market_chart
    try:
        cg_service = CoinGeckoService()
        days_ago = (date.today() - target_date).days
        
        if days_ago < 0:
            logger.warning(f"Data futura solicitada: {target_date}")
            return None
        
        # CoinGecko retorna dados para períodos específicos
        if days_ago == 0:
            period = "1"
        elif days_ago <= 90:
            period = str(days_ago + 1)
        else:
            # Para datas antigas, usar max
            period = "max"
        
        data = cg_service.get_market_chart(coingecko_id, period=f"{period}d")
        
        if not data or 'prices' not in data:
            logger.warning(f"Sem dados de preço para {coingecko_id} em {target_date}")
            return None
        
        # Dados vêm como [[timestamp_ms, price], ...]
        prices = data['prices']
        
        # Encontrar o preço mais próximo da data solicitada
        target_timestamp = datetime.combine(target_date, datetime.min.time()).timestamp() * 1000
        
        closest_price = None
        min_diff = float('inf')
        
        for ts, price in prices:
            diff = abs(ts - target_timestamp)
            if diff < min_diff:
                min_diff = diff
                closest_price = price
        
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
    
    # Buscar da BD em batch
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
    
    result = {int(row['asset_id']): float(row['price_eur']) for _, row in df.iterrows()}
    
    # Para assets sem preço, buscar individualmente (pode ser otimizado)
    missing = [aid for aid in asset_ids if aid not in result]
    for aid in missing:
        price = get_historical_price(aid, target_date)
        if price:
            result[aid] = price
    
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
