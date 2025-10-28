"""Cliente simples para a API pública CoinGecko.

Contractos principais:
- get_price_by_symbol(symbols: list[str], vs_currency: str = 'eur') -> dict
  Retorna um dicionário {"SYM": price_float, ...} para os símbolos pedidos.

Implementação:
- Tenta mapear símbolo para `id` do CoinGecko usando um mapeamento interno para os tokens mais comuns.
- Se não encontrar, consulta `/coins/list` e faz correspondência por `symbol` (case-insensitive).
- Usa `/simple/price` para obter preços em massa.
- Tem caching in-memory simples para o mapeamento símbolo->id e respostas de `/coins/list`.
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

# Simple in-memory caches
_coin_list_cache: Optional[List[Dict]] = None
_symbol_to_id_cache: Dict[str, str] = {k.upper(): v for k, v in COMMON_SYMBOL_MAP.items()}


def _get_coin_list() -> List[Dict]:
    """Retorna a lista de moedas do CoinGecko e faz cache in-memory por enquanto."""
    global _coin_list_cache
    if _coin_list_cache is not None:
        return _coin_list_cache

    url = f"{BASE_URL}/coins/list"
    # Retry on transient errors (including 429) with short backoff
    retries = 3
    backoff = 1.0
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            _coin_list_cache = resp.json()
            return _coin_list_cache
        except requests.RequestException as e:
            logger.warning("Tentativa %d: erro ao buscar coin list do CoinGecko: %s", attempt + 1, e)
            if attempt < retries - 1:
                time.sleep(backoff)
                backoff *= 2
            else:
                logger.error("Erro ao buscar coin list do CoinGecko após %d tentativas: %s", retries, e)
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
    retries = 3
    backoff = 1.0
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            # Preenche o resultado por símbolo original
            for sym, coin_id in symbol_id_map.items():
                if coin_id and coin_id in data and vs_currency in data[coin_id]:
                    prices[sym] = float(data[coin_id][vs_currency])
                else:
                    prices[sym] = None

            return prices
        except requests.RequestException as e:
            # On 429 or similar, wait and retry a few times
            logger.warning("Tentativa %d: Erro ao obter preços do CoinGecko: %s", attempt + 1, e)
            if attempt < retries - 1:
                time.sleep(backoff)
                backoff *= 2
                continue
            logger.error("Erro ao obter preços do CoinGecko após %d tentativas: %s", retries, e)
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
        # simple instance cache
        # cache: key -> (ts, data)
        self._price_cache = {}

        # TTL in seconds for price cache
        self._price_cache_ttl = 30

    def get_prices(self, symbols: List[str], vs_currencies: List[str]):
        """Obter preços para uma lista de símbolos em várias moedas.

        vs_currencies: list like ['eur','usd']
        Returns dict: {symbol: {vs: price, ...}, ...}
        """
        if not symbols:
            return {}

        # Build cache key from symbols and vs_currencies
        key = ("|".join(sorted([s.upper() for s in symbols])), "|".join(sorted([v.lower() for v in vs_currencies])))
        now = time.time()
        cached = self._price_cache.get(key)
        if cached and now - cached[0] < self._price_cache_ttl:
            return cached[1]

        # reutiliza a função get_price_by_symbol para cada vs_currency
        result = {s: {} for s in symbols}
        for vs in vs_currencies:
            prices = get_price_by_symbol(symbols, vs_currency=vs)
            for s, p in prices.items():
                result[s][vs] = p

        # store in cache
        self._price_cache[key] = (now, result)
        return result

    def get_market_chart(self, symbol_or_id: str, period: str = "30d"):
        """Retorna os dados de market_chart para a moeda indicada.

        symbol_or_id: pode ser símbolo (BTC) ou id (bitcoin). Tentamos mapear se for símbolo.
        period: '24h', '7d', '30d', '90d', '1y', 'max'
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
        params = {"vs_currency": "usd", "days": days}
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
