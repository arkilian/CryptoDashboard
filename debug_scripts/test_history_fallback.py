from datetime import date
import logging
from services.coingecko import get_historical_price_by_id

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

coin_id = "archerswap-hunter"
for d in [date(2025, 8, 6), date(2025, 8, 7)]:
    price = get_historical_price_by_id(coin_id, d, vs_currency="eur")
    print(f"{coin_id} @ {d}: {price}")
