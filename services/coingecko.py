"""Cliente simples para a API pública CoinGecko.

Contractos principais:
- get_price_by_symbol(symbols: list[str], vs_currency: str = 'eur') -> dict
  Retorna um dicionário {"SYM": price_float, ...} para os símbolos pedidos.

Implementação:
- Tenta mapear símbolo para `id` do CoinGecko usando um mapeamento interno para os tokens mais comuns.
- Se não encontrar, consulta `/coins/list` e faz correspondência por `symbol` (case-insensitive).
- Usa `/simple/price` para obter preços em massa.
- Tem caching in-memory com TTL para reduzir chamadas à API.
"""
from typing import List, Dict, Optional
import requests
import time
import logging

logger = logging.getLogger(__name__)

# URL base da API CoinGecko (sem API key necessária para endpoints públicos)
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

# Rate limiter global - garantir mínimo de 4 segundos entre QUALQUER chamada API
_last_api_call_time = 0
_min_delay_between_calls = 4.0  # segundos - aumentado para evitar 429 errors


def _get_coin_list() -> List[Dict]:
    """Retorna a lista de moedas do CoinGecko com cache de 1 hora."""
    global _coin_list_cache
    now = time.time()
    
    # Check cache validity
    if _coin_list_cache is not None:
        cache_time, cached_data = _coin_list_cache
        if now - cache_time < _coin_list_cache_ttl:
            return cached_data

    url = f"{BASE_URL}/coins/list"
    # Retry on transient errors (including 429) with short backoff
    retries = 3
    backoff = 3.0  # Aumentado para 3s para evitar rate limits
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=10)
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


def get_price_by_symbol(symbols: List[str], vs_currency: str = "eur") -> Dict[str, Optional[float]]:
    """Obtém preços para uma lista de símbolos.

    Retorna um dict com chave símbolo (original case) e valor float do preço ou None se não disponível.
    """
    if not symbols:
        return {}

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
    url = f"{BASE_URL}/simple/price"

    # Retry on transient errors (e.g., 429) with exponential backoff
    retries = 5
    backoff = 3.0
    for attempt in range(retries):
        try:
            # Rate limiter global - garantir delay mínimo entre chamadas
            global _last_api_call_time
            current_time = time.time()
            time_since_last_call = current_time - _last_api_call_time
            if time_since_last_call < _min_delay_between_calls:
                wait_time = _min_delay_between_calls - time_since_last_call
                logger.info(f"⏱️ Rate limiter: aguardando {wait_time:.2f}s antes da chamada API")
                time.sleep(wait_time)
            
            # Adicionar delay ANTES da chamada para evitar burst
            if attempt > 0:
                time.sleep(backoff)
            
            _last_api_call_time = time.time()  # Atualizar timestamp
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            # Preenche o resultado por símbolo original
            for sym, coin_id in symbol_id_map.items():
                if coin_id and coin_id in data and vs_currency in data[coin_id]:
                    prices[sym] = float(data[coin_id][vs_currency])
                else:
                    prices[sym] = None

            # Guardar no cache
            _price_cache[cache_key] = (time.time(), prices)
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

        url = f"{BASE_URL}/coins/{coin_id}/market_chart"
        params = {"vs_currency": vs_currency, "days": days}
        retries = 3
        backoff = 1.0
        for attempt in range(retries):
            try:
                resp = requests.get(url, params=params, timeout=15)
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
