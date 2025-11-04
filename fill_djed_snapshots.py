"""Preencher snapshots de preços para DJED (e variantes)."""
from datetime import date, timedelta
from services.snapshots import populate_snapshots_for_period
from database.connection import get_engine
import pandas as pd

engine = get_engine()

# Buscar assets que usam 'djed' coingecko_id
df = pd.read_sql(
    "SELECT asset_id, symbol, name FROM t_assets WHERE coingecko_id = 'djed'",
    engine
)

if df.empty:
    print("❌ Nenhum asset com coingecko_id='djed' encontrado")
else:
    print(f"✅ Encontrados {len(df)} assets com coingecko_id='djed':")
    for _, row in df.iterrows():
        symbol_short = row['symbol'][:30] + "..." if len(str(row['symbol'])) > 30 else row['symbol']
        print(f"  - {symbol_short} ({row['name']})")
    
    asset_ids = df['asset_id'].tolist()
    
    # Preencher últimos 30 dias
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    print(f"\n🔄 Preenchendo snapshots de {start_date} até {end_date}...")
    print("   (Isto pode demorar alguns minutos devido ao rate limiting)")
    
    try:
        populate_snapshots_for_period(start_date, end_date, asset_ids)
        print("\n✅ Snapshots preenchidos com sucesso!")
    except Exception as e:
        print(f"\n⚠️ Erro ao preencher snapshots: {e}")
