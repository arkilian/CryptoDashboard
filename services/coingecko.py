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
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        _coin_list_cache = resp.json()
        return _coin_list_cache
    except requests.RequestException as e:
        logger.error("Erro ao buscar coin list do CoinGecko: %s", e)
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
        logger.error("Erro ao obter preços do CoinGecko: %s", e)
        # Em caso de erro, devolve None para todos
        return {s: None for s in symbols}


if __name__ == "__main__":
    # Quick manual test (não executa em import)
    test_symbols = ["BTC", "ETH", "ADA", "NONEXISTENT"]
    print(get_price_by_symbol(test_symbols, "eur"))
