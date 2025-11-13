"""Serviço para gestão de snapshots de preços históricos.

Este módulo permite:
- Buscar preços históricos do CoinGecko e armazená-los localmente
- Consultar preços históricos da base de dados
- Preencher gaps de dados históricos
- Atualizar preços diários automaticamente
"""
import logging
import threading
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
from sqlalchemy import text
from database.connection import get_engine
from services.coingecko import CoinGeckoService, get_current_price_by_id, get_historical_price_by_id, resolve_coingecko_id_for_symbol
import time
import requests

logger = logging.getLogger(__name__)

# Background control for snapshot population
_bg_snapshots_thread: Optional[threading.Thread] = None
_bg_stop_event: Optional[threading.Event] = None

# URL base da API CoinGecko
BASE_URL = "https://api.coingecko.com/api/v3"

# Cache global para evitar chamadas repetidas durante mesma execução
_prices_session_cache = {}  # {(symbol, date): price}

# Proteção contra rate limit abuse
_coingecko_429_counter = 0
_coingecko_429_threshold = 3  # Após 3 erros 429 consecutivos, desabilitar temporariamente
_coingecko_disabled_until = None  # Timestamp de quando reabilitar


def _is_coingecko_available() -> bool:
    """Verifica se a API CoinGecko está disponível (não bloqueada por 429s repetidos)."""
    global _coingecko_disabled_until, _coingecko_429_counter
    
    if _coingecko_disabled_until is None:
        return True
    
    # Verificar se já passou o tempo de cooldown (5 minutos)
    if datetime.now() >= _coingecko_disabled_until:
        logger.info("✅ CoinGecko reabilitada após cooldown")
        _coingecko_disabled_until = None
        _coingecko_429_counter = 0
        return True
    
    return False


def _handle_coingecko_error(error: Exception):
    """Regista erro da CoinGecko e atualiza contador de 429s."""
    global _coingecko_429_counter, _coingecko_disabled_until
    
    # Verificar se é erro 429
    is_429 = False
    if isinstance(error, requests.exceptions.HTTPError):
        if hasattr(error, 'response') and error.response is not None:
            is_429 = error.response.status_code == 429
    elif "429" in str(error) or "rate limit" in str(error).lower():
        is_429 = True
    
    if is_429:
        _coingecko_429_counter += 1
        logger.warning(f"⚠️ CoinGecko 429 (rate limit) #{_coingecko_429_counter}/{_coingecko_429_threshold}")
        
        if _coingecko_429_counter >= _coingecko_429_threshold:
            _coingecko_disabled_until = datetime.now() + timedelta(minutes=5)
            logger.error(
                f"❌ CoinGecko desabilitada temporariamente até {_coingecko_disabled_until.strftime('%H:%M:%S')} "
                f"devido a {_coingecko_429_counter} erros 429 consecutivos"
            )
    else:
        # Reset contador em caso de erro diferente
        _coingecko_429_counter = 0


def _reset_coingecko_429_counter():
    """Reset contador após chamada bem-sucedida."""
    global _coingecko_429_counter
    if _coingecko_429_counter > 0:
        logger.info("✅ CoinGecko respondeu com sucesso - reset contador 429")
        _coingecko_429_counter = 0


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
    
    # Buscar symbol e coingecko_id ANTES de fazer logging ou chamada API
    df_asset = pd.read_sql(
        "SELECT symbol, coingecko_id, is_stablecoin FROM t_assets WHERE asset_id = %s",
        engine,
        params=(asset_id,)
    )
    
    if df_asset.empty:
        logger.warning(f"Asset {asset_id} não encontrado")
        return None
    
    symbol = df_asset.iloc[0]['symbol']
    coingecko_id = df_asset.iloc[0]['coingecko_id']
    
    # Se não encontrar, buscar do CoinGecko e guardar
    logger.info(f"💰 Preço não encontrado localmente para {symbol} (asset_id={asset_id}) em {target_date}. Buscando do CoinGecko...")
    
    # Se não tem coingecko_id, verificar se é EUR (moeda FIAT base)
    if not coingecko_id:
        
        # Apenas EUR (moeda base) tem preço fixo de 1.0
        if symbol == 'EUR':
            # Guardar preço fixo de 1.0 para EUR
            try:
                with engine.begin() as conn:
                    conn.execute(
                        text("""
                            INSERT INTO t_price_snapshots (asset_id, snapshot_date, price_eur, source)
                            VALUES (:asset_id, :date, 1.0, 'fixed')
                            ON CONFLICT (asset_id, snapshot_date) DO NOTHING
                        """),
                        {"asset_id": asset_id, "date": target_date}
                    )
            except Exception as e:
                logger.warning(f"Erro ao guardar preço fixo: {e}")
            return 1.0
        
        # Qualquer outro ativo sem coingecko_id (incluindo stablecoins) é erro de configuração
        logger.warning(f"Asset {asset_id} ({symbol}) não tem coingecko_id configurado")
        return None
    
    coingecko_id = df_asset.iloc[0]['coingecko_id']
    
    # Verificar se CoinGecko está disponível
    if not _is_coingecko_available():
        logger.warning(f"⏳ CoinGecko desabilitada - pulando preço para {coingecko_id} em {target_date}")
        return None
    
    # Buscar preço histórico do CoinGecko usando endpoint de histórico por data específica
    try:
        # Centralized rate limiting via services.coingecko helpers
        days_ago = (date.today() - target_date).days
        if days_ago < 0:
            logger.warning(f"Data futura solicitada: {target_date}")
            return None

        if days_ago == 0:
            price = get_current_price_by_id(coingecko_id, vs_currency="eur")
            if price is None:
                logger.warning(f"Preço atual não disponível para {coingecko_id}")
                return None
            closest_price = float(price)
        else:
            price = get_historical_price_by_id(coingecko_id, target_date, vs_currency="eur")
            if price is None:
                logger.warning(f"Preço histórico não disponível para {coingecko_id} em {target_date}")
                return None
            closest_price = float(price)
        
        # Sucesso - reset contador de erros 429
        _reset_coingecko_429_counter()
        
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
        _handle_coingecko_error(e)
        logger.error(f"Erro ao buscar preço histórico do CoinGecko: {e}")
    
    return None


def get_historical_prices_bulk(asset_ids: List[int], target_date: date, allow_api_fallback: bool = True) -> Dict[int, float]:
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
    
    # Para assets sem preço na BD, buscar do CoinGecko
    missing = [aid for aid in asset_ids if aid not in result]
    if missing and allow_api_fallback:
        logger.info(f"🌐 Buscando {len(missing)} preços em falta do CoinGecko para {target_date}...")
        
        # Rate limiting is handled globally in coingecko.py and get_historical_price
        for aid in missing:
            price = get_historical_price(aid, target_date)  # Busca CoinGecko e guarda na BD
            if price:
                result[aid] = price
    
    return result


def get_historical_prices_by_symbol(symbols: List[str], target_date: date, allow_api_fallback: bool = True) -> Dict[str, float]:
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
    
    # Buscar asset_ids por símbolo OU por nome (maior cobertura)
    placeholders = ','.join(['%s'] * len(missing_symbols))
    df_assets = pd.read_sql(
        f"""
        SELECT asset_id, symbol, name 
        FROM t_assets 
        WHERE UPPER(symbol) IN ({placeholders})
           OR UPPER(name)   IN ({placeholders})
        """,
        engine,
        params=tuple([s.upper() for s in missing_symbols] + [s.upper() for s in missing_symbols])
    )
    
    if df_assets.empty:
        return result
    
    # Mapear symbol -> asset_id efficiently using pandas to_dict
    # Preferir mapear por symbol; se não existir, usar name match
    symbol_to_id = {}
    for _, r in df_assets.iterrows():
        sym = str(r['symbol']).upper() if pd.notna(r['symbol']) else None
        nm = str(r['name']).upper() if pd.notna(r['name']) else None
        aid = int(r['asset_id'])
        if sym and sym in [s.upper() for s in missing_symbols]:
            symbol_to_id[sym] = aid
        if nm and nm in [s.upper() for s in missing_symbols] and nm not in symbol_to_id:
            symbol_to_id[nm] = aid

    # Criar mapeamento na mesma casing dos missing_symbols originais
    symbol_to_id = {orig: symbol_to_id.get(orig.upper()) for orig in missing_symbols if symbol_to_id.get(orig.upper())}
    asset_ids = list(symbol_to_id.values())
    
    # Buscar preços históricos por asset_id (com rate limiting)
    prices_by_id = get_historical_prices_bulk(asset_ids, target_date, allow_api_fallback=allow_api_fallback)
    
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
    
    logger.info(f"📅 populate_snapshots_for_period: {start_date} até {end_date} para {len(asset_ids)} ativos")
    
    # Iterar por cada dia
    current = start_date
    day_count = 0
    total_days = (end_date - start_date).days + 1
    
    global _bg_stop_event
    while current <= end_date:
        if _bg_stop_event and _bg_stop_event.is_set():
            logger.warning("⏹️ Snapshot population cancelled by user")
            break
        day_count += 1
        logger.info(f"Processando {current} ({day_count}/{total_days})...")
        
        # Process assets in smaller batches to avoid overwhelming API
        batch_size = 5  # Reduced from processing all at once
        for i in range(0, len(asset_ids), batch_size):
            batch = asset_ids[i:i+batch_size]
            logger.info(f"  📦 Lote {i//batch_size + 1}/{(len(asset_ids) + batch_size - 1)//batch_size} ({len(batch)} ativos)")
            
            for asset_id in batch:
                if _bg_stop_event and _bg_stop_event.is_set():
                    logger.warning("⏹️ Snapshot population cancelled during batch")
                    break
                try:
                    get_historical_price(asset_id, current)
                except Exception as e:
                    logger.warning(f"  ⚠️ Erro ao buscar preço para asset_id={asset_id}: {e}")
            
            # Small delay between batches to avoid rate limits
            if i + batch_size < len(asset_ids):
                time.sleep(0.5)  # 500ms between batches
        
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


# ---------- Helpers used by Cardano sync to ensure assets and snapshots ----------
def ensure_assets_for_symbols(symbols: List[str], chain: str = "Cardano") -> Dict[str, int]:
    """Ensure rows exist in t_assets for provided symbols.

    If an asset is missing, insert it and try to resolve coingecko_id by symbol.
    Returns mapping {symbol: asset_id} for all provided symbols that exist after ensuring.
    """
    if not symbols:
        return {}
    engine = get_engine()
    out: Dict[str, int] = {}
    # Normalize symbols list (unique, non-empty)
    symbols_norm = [s for s in sorted(set([str(s).strip() for s in symbols])) if s]
    if not symbols_norm:
        return {}

    # Query existing
    placeholders = ','.join(['%s'] * len(symbols_norm))
    df = pd.read_sql(
        f"""
        SELECT asset_id, symbol, coingecko_id FROM t_assets WHERE UPPER(symbol) IN ({placeholders})
        """,
        engine,
        params=tuple([s.upper() for s in symbols_norm])
    )
    existing = {str(r['symbol']).upper(): int(r['asset_id']) for _, r in df.iterrows()}
    for s in symbols_norm:
        if s.upper() in existing:
            out[s] = existing[s.upper()]

    # Insert missing
    missing = [s for s in symbols_norm if s.upper() not in existing]
    if missing:
        # Try resolve coingecko id for each symbol
        rows = []
        for s in missing:
            cg_id = resolve_coingecko_id_for_symbol(s)
            rows.append({
                'symbol': s,
                'name': s,
                'chain': chain,
                'coingecko_id': cg_id,
                'is_stablecoin': False,
            })
        # Bulk insert
        try:
            with engine.begin() as conn:
                for r in rows:
                    conn.execute(
                        text("""
                            INSERT INTO t_assets (symbol, name, chain, coingecko_id, is_stablecoin)
                            VALUES (:symbol, :name, :chain, :coingecko_id, :is_stablecoin)
                            ON CONFLICT (symbol) DO UPDATE
                            SET name = COALESCE(EXCLUDED.name, t_assets.name),
                                chain = COALESCE(EXCLUDED.chain, t_assets.chain),
                                coingecko_id = COALESCE(EXCLUDED.coingecko_id, t_assets.coingecko_id)
                        """), r)
        except Exception as e:
            logger.warning(f"Erro ao inserir ativos em t_assets: {e}")

        # Requery to get asset_ids
        df2 = pd.read_sql(
            f"""
            SELECT asset_id, symbol FROM t_assets WHERE UPPER(symbol) IN ({placeholders})
            """,
            engine,
            params=tuple([s.upper() for s in symbols_norm])
        )
        for _, r in df2.iterrows():
            out[str(r['symbol'])] = int(r['asset_id'])

    return out


def ensure_assets_and_snapshots(symbols: List[str], start_date: date, end_date: date):
    """Ensure t_assets exist and populate t_price_snapshots for the period for resolvable assets.

    Only assets with a coingecko_id will receive snapshots.
    """
    if not symbols or start_date is None or end_date is None:
        return
    # Ensure assets
    mapping = ensure_assets_for_symbols(symbols, chain="Cardano")
    if not mapping:
        return
    # Filter assets that do have coingecko_id
    engine = get_engine()
    placeholders = ','.join(['%s'] * len(mapping))
    df = pd.read_sql(
        f"""
        SELECT asset_id FROM t_assets 
        WHERE asset_id IN ({placeholders}) AND coingecko_id IS NOT NULL
        """,
        engine,
        params=tuple(mapping.values())
    )
    asset_ids = [int(aid) for aid in df['asset_id'].tolist()]
    if not asset_ids:
        return
    # Populate snapshots for this period
    try:
        populate_snapshots_for_period(start_date, end_date, asset_ids)
    except Exception as e:
        logger.warning(f"Erro ao popular snapshots para período {start_date}..{end_date}: {e}")


def start_ensure_assets_and_snapshots_async(symbols: List[str], start_date: date, end_date: date) -> bool:
    """Inicia o ensure_assets_and_snapshots em background para não bloquear a UI.

    Retorna True se a thread foi iniciada.
    """
    global _bg_snapshots_thread, _bg_stop_event
    try:
        if not symbols or start_date is None or end_date is None:
            return False

        def _runner():
            try:
                logger.info(
                    f"🚀 (BG) A garantir ativos e snapshots para {len(symbols)} símbolos entre {start_date} e {end_date}"
                )
                ensure_assets_and_snapshots(symbols, start_date, end_date)
                logger.info("✅ (BG) Ativos e snapshots processados")
            except Exception as e:
                logger.warning(f"⚠️ (BG) Falha ao processar snapshots: {e}")

        _bg_stop_event = threading.Event()
        t = threading.Thread(target=_runner, daemon=True)
        _bg_snapshots_thread = t
        t.start()
        return True
    except Exception:
        return False


def cancel_background_snapshots() -> bool:
    """Signal cancellation and attempt to stop background snapshot population."""
    global _bg_snapshots_thread, _bg_stop_event
    try:
        if _bg_stop_event:
            _bg_stop_event.set()
        return True
    except Exception:
        return False
