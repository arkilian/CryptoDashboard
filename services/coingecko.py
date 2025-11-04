"""Cliente simples para a API pública CoinGecko.

Contractos principais:
- get_price_by_symbol(symbols: list[str], vs_currency: str = 'eur') -> dict
  Retorna um dicionário {"SYM": price_float, ...} para os símbolos pedidos.

Implementação:
- Tenta mapear símbolo para `id` do CoinGecko usando um mapeamento interno para os tokens mais comuns.
- Se não encontrar, consulta `/coins/list` e faz correspondência por `symbol` (case-insensitive).
- Usa `/simple/price` para obter preços em massa.
- Tem caching in-memory com TTL para reduzir chamadas à API.
- Lê configuração (rate_limit, api_key) da tabela t_api_coingecko para ajustar comportamento.
"""
from typing import List, Dict, Optional
from datetime import date
import requests
import time
import logging

logger = logging.getLogger(__name__)

# ---------- Dynamic config from DB ----------
_coingecko_config_cache: Optional[tuple] = None  # (timestamp, config_dict)
_coingecko_config_cache_ttl = 300  # 5 minutos


def _get_coingecko_config() -> Optional[Dict]:
    """Fetch active CoinGecko API config from t_api_coingecko.
    
    Returns dict with keys: api_key, base_url, rate_limit, timeout, or None if not configured.
    Cached for 5 minutes to avoid repeated DB queries.
    """
    global _coingecko_config_cache
    now = time.time()
    if _coingecko_config_cache is not None:
        cache_time, cached = _coingecko_config_cache
        if now - cache_time < _coingecko_config_cache_ttl:
            return cached
    
    try:
        from database.api_config import get_active_coingecko_apis
        apis = get_active_coingecko_apis()
        if apis:
            config = apis[0]  # Use the first active config
            _coingecko_config_cache = (now, config)
            # Log config info (sem expor API key completa)
            has_key = bool(config.get('api_key'))
            rate = config.get('rate_limit', 'N/A')
            url = config.get('base_url', 'N/A')
            logger.info(f"📋 CoinGecko config: API Key={'✓' if has_key else '✗'}, Rate={rate}/min, URL={url}")
            return config
    except Exception as e:
        logger.warning(f"Erro ao buscar config CoinGecko da DB: {e}")
    return None

# URL base da API CoinGecko (sem API key necessária para endpoints públicos)
# Será substituído dinamicamente pela config da DB se disponível
BASE_URL = "https://api.coingecko.com/api/v3"

# Mapeamento rápido para moedas/tokens comuns: symbol (uppercase) -> coingecko id
COMMON_SYMBOL_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "ADA": "cardano",
    "SOL": "solana",
    "XRP": "ripple",
    "LTC": "litecoin",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "BNB": "binancecoin",
    "USDT": "tether",
    "USDC": "usd-coin",
    "BCH": "bitcoin-cash",
}

# Cache with TTL
_coin_list_cache: Optional[tuple] = None  # (timestamp, data)
_coin_list_cache_ttl = 3600  # 1 hour
_symbol_to_id_cache: Dict[str, str] = {k.upper(): v for k, v in COMMON_SYMBOL_MAP.items()}

# Cache de preços com TTL mais longo para evitar rate limits
_price_cache: Dict[str, tuple] = {}  # {cache_key: (timestamp, prices_dict)}
_price_cache_ttl = 300  # 5 minutos - aumentado para reduzir chamadas API

# Rate limiter global - garantir mínimo de X segundos entre QUALQUER chamada API
# Valores base (podem ser sobrescritos pela config da DB)
_last_api_call_time = 0
_min_delay_between_calls = 4.0  # segundos - aumentado para evitar 429 errors

# Global pause flag to stop any external CoinGecko calls when requested
_coingecko_paused = False


def _get_rate_limit_delay() -> float:
    """Calculate minimum delay between API calls based on DB config.
    
    Returns delay in seconds. Uses EXACT value from DB: delay = 60 / rate_limit.
    Adds only a minimal floor to avoid zero/invalid values.
    """
    config = _get_coingecko_config()
    if config and config.get('rate_limit'):
        try:
            rate_limit = int(config['rate_limit'])
        except Exception:
            rate_limit = None
        if rate_limit and rate_limit > 0:
            # Exact delay based on DB value
            return max(60.0 / rate_limit, 0.5)
    # Fallback when config missing
    return 2.0


def invalidate_coingecko_config_cache():
    """Invalidate cached CoinGecko config so new DB values apply immediately."""
    global _coingecko_config_cache
    _coingecko_config_cache = None
    logger.info("🧹 CoinGecko config cache invalidated")


def pause_coingecko_requests():
    """Pause all outgoing CoinGecko HTTP calls."""
    global _coingecko_paused
    _coingecko_paused = True
    logger.warning("⏸️ CoinGecko requests PAUSED")


def resume_coingecko_requests():
    """Resume outgoing CoinGecko HTTP calls."""
    global _coingecko_paused
    _coingecko_paused = False
    logger.info("▶️ CoinGecko requests RESUMED")


def _is_coingecko_enabled() -> bool:
    """Return True if there is an active config and we are not paused."""
    if _coingecko_paused:
        return False
    return _get_coingecko_config() is not None


def invalidate_coingecko_config_cache():
    """Invalidate cached CoinGecko config so new DB values apply immediately."""
    global _coingecko_config_cache
    _coingecko_config_cache = None
    logger.info("🧹 CoinGecko config cache invalidated")


def _get_headers() -> Dict[str, str]:
    """Build request headers, including Authorization if api_key is configured.
    
    CoinGecko has different authentication methods:
    - Demo tier: API key goes as query parameter (x_cg_demo_api_key)
    - Pro tier: API key goes as header (x-cg-pro-api-key)
    
    For Demo API, we return empty headers and add api_key to URL params instead.
    """
    headers = {"Accept": "application/json"}
    config = _get_coingecko_config()
    
    if config and config.get('api_key'):
        api_key = config['api_key']
        
        # Pro API key goes in header
        if not api_key.startswith('CG-'):
            headers["x-cg-pro-api-key"] = api_key
            logger.debug(f"🔑 Pro API Key configurada no header: {api_key[:8]}...")
    
    return headers


def _add_api_key_to_params(params: dict) -> dict:
    """Add API key to query parameters if using Demo API.
    
    Demo API keys (starting with CG-) must be sent as query parameter.
    """
    config = _get_coingecko_config()
    
    if config and config.get('api_key'):
        api_key = config['api_key']
        
        # Demo API key goes in URL params
        if api_key.startswith('CG-'):
            params['x_cg_demo_api_key'] = api_key
            logger.debug(f"🔑 Demo API Key adicionada aos params: {api_key[:8]}...")
    
    return params


def _get_base_url() -> str:
    """Get base URL from DB config or fallback to public API.
    
    Note: CoinGecko Pro API uses https://pro-api.coingecko.com/api/v3
          Demo/Free API uses https://api.coingecko.com/api/v3
    """
    config = _get_coingecko_config()
    if config:
        # Se tem API key configurada, verificar se URL base está correta
        if config.get('api_key') and config.get('base_url'):
            base_url = config['base_url']
            api_key = config['api_key']
            
            # Demo API (CG-xxx) deve usar URL pública - está correto
            if api_key.startswith('CG-'):
                if 'pro-api' in base_url:
                    logger.warning(
                        "⚠️ Demo API Key configurada mas base_url é pro-api. "
                        "Para Demo API, use: https://api.coingecko.com/api/v3"
                    )
            # Pro API deve usar pro-api URL
            elif 'pro-api' not in base_url:
                logger.warning(
                    "⚠️ Pro API Key configurada mas base_url não é pro-api.coingecko.com. "
                    "Para CoinGecko Pro, use: https://pro-api.coingecko.com/api/v3"
                )
            return base_url
        elif config.get('base_url'):
            return config['base_url']
    return BASE_URL


def _get_coin_list() -> List[Dict]:
    """Retorna a lista de moedas do CoinGecko com cache de 1 hora."""
    global _coin_list_cache
    now = time.time()
    
    # Check cache validity
    if _coin_list_cache is not None:
        cache_time, cached_data = _coin_list_cache
        if now - cache_time < _coin_list_cache_ttl:
            return cached_data

    url = f"{_get_base_url()}/coins/list"
    # Retry on transient errors (including 429) with short backoff
    retries = 3
    backoff = 3.0  # Aumentado para 3s para evitar rate limits
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=_get_headers(), timeout=10)
            resp.raise_for_status()
            data = resp.json()
            _coin_list_cache = (now, data)
            return data
        except requests.RequestException as e:
            logger.warning("Tentativa %d: erro ao buscar coin list do CoinGecko: %s", attempt + 1, e)
            if attempt < retries - 1:
                time.sleep(backoff)
                backoff *= 2
            else:
                logger.error("Erro ao buscar coin list do CoinGecko após %d tentativas: %s", retries, e)
                # Return old cache if available
                if _coin_list_cache is not None:
                    logger.info("Usando cache expirado da coin list")
                    return _coin_list_cache[1]
                return []


def _symbol_to_id(symbol: str) -> Optional[str]:
    """Mapeia símbolo para CoinGecko id. Retorna None se não conseguir mapear."""
    sym = symbol.upper()
    if sym in _symbol_to_id_cache:
        return _symbol_to_id_cache[sym]

    coins = _get_coin_list()
    if not coins:
        return None

    # Busca a primeira correspondência por symbol (case-insensitive)
    for c in coins:
        if c.get("symbol", "").upper() == sym:
            coin_id = c.get("id")
            _symbol_to_id_cache[sym] = coin_id
            return coin_id

    return None


def resolve_coingecko_id_for_symbol(symbol: str) -> Optional[str]:
    """Public wrapper to resolve a CoinGecko ID for a given symbol (case-insensitive).

    Returns None if no mapping was found.
    """
    return _symbol_to_id(symbol)


def get_price_by_symbol(symbols: List[str], vs_currency: str = "eur") -> Dict[str, Optional[float]]:
    """Obtém preços para uma lista de símbolos.

    Retorna um dict com chave símbolo (original case) e valor float do preço ou None se não disponível.
    """
    if not symbols:
        return {}

    # If CoinGecko is disabled/paused, return None for all
    if not _is_coingecko_enabled():
        logger.info("CoinGecko disabled/paused - skipping get_price_by_symbol")
        return {s: None for s in symbols}

    # Criar cache key baseado nos símbolos e moeda
    cache_key = f"{'-'.join(sorted(symbols))}_{vs_currency}"
    now = time.time()
    
    # Verificar cache de preços
    if cache_key in _price_cache:
        cache_time, cached_prices = _price_cache[cache_key]
        if now - cache_time < _price_cache_ttl:
            logger.info(f"💾 Cache HIT para preços: {symbols[:3]}{'...' if len(symbols) > 3 else ''}")
            return cached_prices

    logger.info(f"🔍 Cache MISS - chamando API para {symbols[:3]}{'...' if len(symbols) > 3 else ''}")

    # Mapeia símbolos para ids
    symbol_id_map: Dict[str, str] = {}
    ids = []
    for s in symbols:
        coin_id = _symbol_to_id(s)
        if coin_id:
            symbol_id_map[s] = coin_id
            ids.append(coin_id)
        else:
            symbol_id_map[s] = None

    prices: Dict[str, Optional[float]] = {s: None for s in symbols}
    if not ids:
        return prices

    # Chamada ao endpoint /simple/price
    params = {
        "ids": ",".join(ids),
        "vs_currencies": vs_currency,
    }
    # Add API key to params if using Demo API
    params = _add_api_key_to_params(params)
    
    url = f"{_get_base_url()}/simple/price"

    # Retry on transient errors (e.g., 429) with exponential backoff
    retries = 5
    backoff = 3.0
    for attempt in range(retries):
        try:
            # Rate limiter global - garantir delay mínimo entre chamadas (dinâmico)
            global _last_api_call_time
            current_time = time.time()
            time_since_last_call = current_time - _last_api_call_time
            min_delay = _get_rate_limit_delay()
            if time_since_last_call < min_delay:
                wait_time = min_delay - time_since_last_call
                logger.info(f"⏱️ Rate limiter: aguardando {wait_time:.2f}s antes da chamada API")
                time.sleep(wait_time)
            
            # Adicionar delay ANTES da chamada para evitar burst
            if attempt > 0:
                time.sleep(backoff)
            
            _last_api_call_time = time.time()  # Atualizar timestamp
            cache_timestamp = _last_api_call_time  # Capture timestamp for cache
            # If paused mid-flight, abort before issuing request
            if not _is_coingecko_enabled():
                logger.info("CoinGecko disabled/paused mid-call - aborting request")
                return {s: None for s in symbols}
            resp = requests.get(url, params=params, headers=_get_headers(), timeout=15)
            resp.raise_for_status()
            data = resp.json()

            # Preenche o resultado por símbolo original
            for sym, coin_id in symbol_id_map.items():
                if coin_id and coin_id in data and vs_currency in data[coin_id]:
                    prices[sym] = float(data[coin_id][vs_currency])
                else:
                    prices[sym] = None

            # Guardar no cache
            _price_cache[cache_key] = (cache_timestamp, prices)
            logger.info(f"✅ Preços obtidos da API: {symbols[:3]}{'...' if len(symbols) > 3 else ''}")
            
            return prices
            
        except requests.RequestException as e:
            # On 429 or similar, wait and retry a few times
            logger.warning("Tentativa %d/%d: Erro ao obter preços do CoinGecko: %s", attempt + 1, retries, e)
            if attempt < retries - 1:
                backoff *= 2.5  # Exponencial mais agressivo
                continue
            
            # Última tentativa falhou - retornar cache expirado se existir
            logger.error("❌ Erro após %d tentativas: %s", retries, e)
            if cache_key in _price_cache:
                _, expired_prices = _price_cache[cache_key]
                logger.warning("⚠️ Usando cache EXPIRADO para evitar falha total")
                return expired_prices
            
            return {s: None for s in symbols}


if __name__ == "__main__":
    # Quick manual test (não executa em import)
    test_symbols = ["BTC", "ETH", "ADA", "NONEXISTENT"]
    print(get_price_by_symbol(test_symbols, "eur"))


# ---------- Extra helpers for rate-limited, ID-based calls ----------
def _rate_limited_get(url: str, params: Optional[dict] = None, timeout: int = 15, retries: int = 5) -> Optional[dict]:
    """Internal helper to perform a GET with global rate limiting and backoff.

    Returns parsed JSON dict on success, or None on failure after retries.
    """
    global _last_api_call_time
    backoff = 2.0  # Start with 2 seconds
    
    # Add API key to params if using Demo API
    if params is None:
        params = {}
    params = _add_api_key_to_params(params)
    
    for attempt in range(retries):
        try:
            if not _is_coingecko_enabled():
                logger.info("CoinGecko disabled/paused - skipping HTTP GET")
                return None
            # Enforce global min delay between calls (dynamic from DB config)
            now = time.time()
            elapsed = now - _last_api_call_time
            min_delay = _get_rate_limit_delay()
            if elapsed < min_delay:
                wait_time = min_delay - elapsed
                if wait_time > 0.1:  # Only log if significant wait
                    logger.debug(f"⏱️ Rate limiter: aguardando {wait_time:.2f}s")
                time.sleep(wait_time)

            # Additional backoff between retries (exponential)
            if attempt > 0:
                retry_delay = backoff * (2 ** (attempt - 1))
                logger.info(f"⏱️ Retry {attempt}: aguardando {retry_delay:.1f}s antes de tentar novamente")
                time.sleep(retry_delay)

            _last_api_call_time = time.time()
            # If paused mid-flight, abort before issuing request
            if not _is_coingecko_enabled():
                logger.info("CoinGecko disabled/paused mid-call - aborting HTTP GET")
                return None
            resp = requests.get(url, params=params or {}, headers=_get_headers(), timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 429:
                logger.warning(f"⚠️ 429 Rate Limit na tentativa {attempt + 1}/{retries}")
                # For 429, use longer backoff
                if attempt == retries - 1:
                    logger.error(f"❌ Excedido limite de tentativas após 429s repetidos")
                    return None
                # Exponential backoff for 429s: 5s, 10s, 20s, 40s...
                time.sleep(5 * (2 ** attempt))
                continue
            else:
                logger.warning(f"Tentativa {attempt + 1}/{retries}: erro HTTP em chamada CoinGecko: {e}")
        except requests.RequestException as e:
            logger.warning(f"Tentativa {attempt + 1}/{retries}: erro em chamada CoinGecko: {e}")
            if attempt == retries - 1:
                logger.error(f"Falha após {retries} tentativas: {e}")
                return None


def get_current_price_by_id(coin_id: str, vs_currency: str = "eur") -> Optional[float]:
    """Get current price for a specific CoinGecko coin id, with rate limiting and retries."""
    url = f"{_get_base_url()}/simple/price"
    data = _rate_limited_get(url, params={"ids": coin_id, "vs_currencies": vs_currency}, timeout=15, retries=5)
    if not data:
        return None
    try:
        value = data.get(coin_id, {}).get(vs_currency)
        return float(value) if value is not None else None
    except Exception:
        return None


def get_historical_price_by_id(coin_id: str, target_date: date, vs_currency: str = "eur") -> Optional[float]:
    """Get historical price for a specific CoinGecko coin id and date (DD-MM-YYYY), with rate limiting.

    Uses /coins/{id}/history.
    """
    # Format date as DD-MM-YYYY per API
    try:
        date_str = target_date.strftime("%d-%m-%Y")
    except Exception:
        # If a str was passed, assume it's already correct
        date_str = str(target_date)
    url = f"{_get_base_url()}/coins/{coin_id}/history"
    data = _rate_limited_get(url, params={"date": date_str, "localization": "false"}, timeout=20, retries=5)
    if not data:
        return None
    try:
        market_data = data.get("market_data", {})
        current_price = market_data.get("current_price", {})
        value = current_price.get(vs_currency)
        if value is not None:
            return float(value)
        # Fallback: tentar via market_chart quando não há preço direto para a data/moeda
        logger.info(
            f"ℹ️ Sem price em history para id={coin_id}, data={date_str}, vs={vs_currency}. A tentar market_chart..."
        )
        return _get_price_from_market_chart_by_date(coin_id, target_date, vs_currency)
    except Exception as e:
        logger.warning(f"Falha a interpretar /history para {coin_id} em {date_str}: {e}")
        # Último recurso: tentar market_chart
        return _get_price_from_market_chart_by_date(coin_id, target_date, vs_currency)


def _get_price_from_market_chart_by_date(coin_id: str, target_date: date, vs_currency: str = "eur") -> Optional[float]:
    """Fallback para obter preço do dia usando /coins/{id}/market_chart.

    Estratégia:
    - Calcula days = min(90, days_ago+1)
    - Busca série prices e filtra amostras do próprio dia (UTC)
    - Se existirem várias amostras, retorna média do dia
    - Caso não haja amostras do dia, retorna o ponto mais próximo ao meio-dia UTC
    """
    try:
        days_ago = (date.today() - target_date).days
        if days_ago < 0:
            return None
        days = max(1, min(90, days_ago + 1))
        svc = CoinGeckoService()
        mc = svc.get_market_chart(coin_id, period=f"{days}d", vs_currency=vs_currency)
        prices = mc.get("prices") if isinstance(mc, dict) else None
        if not prices:
            return None

        # Normalizar timestamps (ms) -> date e filtrar pelo target_date
        from datetime import datetime as _dt, timezone as _tz
        day_points = []
        target_midday = _dt.combine(target_date, _dt.min.time()).replace(tzinfo=_tz.utc).timestamp() + 12*3600
        for ts_ms, val in prices:
            try:
                d = _dt.utcfromtimestamp(ts_ms / 1000.0).date()
                if d == target_date:
                    day_points.append(float(val))
            except Exception:
                continue

        if day_points:
            avg = sum(day_points) / len(day_points)
            return float(avg)

        # Se não há pontos no próprio dia, pegar o mais próximo do meio-dia do dia alvo
        closest = None
        closest_dt_diff = None
        for ts_ms, val in prices:
            try:
                t = ts_ms / 1000.0
                diff = abs(t - target_midday)
                if closest is None or diff < closest_dt_diff:
                    closest = float(val)
                    closest_dt_diff = diff
            except Exception:
                continue
        return closest
    except Exception as e:
        logger.warning(f"Falha no fallback market_chart para {coin_id} em {target_date}: {e}")
        return None


class CoinGeckoService:
    """Pequeno wrapper orientado a objeto para uso na app.

    Methods:
    - get_prices(symbols, vs_currencies) -> dict
    - get_market_chart(symbol_or_id, period) -> dict (raw response from /coins/{id}/market_chart)
    """

    def __init__(self):
        # simple instance cache with TTL
        # cache: key -> (timestamp, data)
        self._price_cache = {}

        # TTL in seconds for price cache
        self._price_cache_ttl = 30

    def get_prices(self, symbols: List[str], vs_currencies: List[str]):
        """Obter preços para uma lista de símbolos em várias moedas.

        vs_currencies: list like ['eur','usd']
        Returns dict: {symbol: {vs: price, ...}, ...}
        
        NOTA: Usa cache global agora via get_price_by_symbol()
        """
        if not symbols:
            return {}

        # Reutiliza a função get_price_by_symbol (que tem cache global)
        result = {s: {} for s in symbols}
        for vs in vs_currencies:
            prices = get_price_by_symbol(symbols, vs_currency=vs)
            for s, p in prices.items():
                result[s][vs] = p

        return result

    def get_market_chart(self, symbol_or_id: str, period: str = "30d", vs_currency: str = "eur"):
        """Retorna os dados de market_chart para a moeda indicada.

        symbol_or_id: pode ser símbolo (BTC) ou id (bitcoin). Tentamos mapear se for símbolo.
        period: '24h', '7d', '30d', '90d', '1y', 'max'
        vs_currency: moeda de referência (default: 'eur')
        """
        # Mapear período para parâmetro days
        mapping = {
            "24h": "1",
            "7d": "7",
            "30d": "30",
            "90d": "90",
            "1y": "365",
            "max": "max",
        }

        days = mapping.get(period, "30")

        # Tentar descobrir se foi passado id ou símbolo
        coin_id = symbol_or_id
        if len(symbol_or_id) <= 5 and symbol_or_id.isalpha():
            # provável símbolo curto (BTC, ADA)
            mapped = _symbol_to_id(symbol_or_id)
            if mapped:
                coin_id = mapped

        url = f"{_get_base_url()}/coins/{coin_id}/market_chart"
        params = {"vs_currency": vs_currency, "days": days}
        # Add API key to params if using Demo API
        params = _add_api_key_to_params(params)
        
        retries = 3
        backoff = 1.0
        for attempt in range(retries):
            try:
                resp = requests.get(url, params=params, headers=_get_headers(), timeout=15)
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as e:
                logger.warning("Tentativa %d: Erro ao obter market_chart: %s", attempt + 1, e)
                if attempt < retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                logger.error("Erro ao obter market_chart após %d tentativas: %s", retries, e)
                return {}
