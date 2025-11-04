"""
Script para configurar DjedMicroUSD para usar o preço do DJED.

DjedMicroUSD é o token de recibo do Liqwid quando faz lending de DJED.
Podemos usar o preço do DJED para calcular o valor do DjedMicroUSD.
"""

from database.connection import get_connection, return_connection
import pandas as pd

conn = get_connection()
cur = conn.cursor()

# 1. Verificar se DJED existe e tem coingecko_id
print("=" * 60)
print("1. Verificando DJED na base de dados...")
print("=" * 60)

cur.execute("SELECT asset_id, symbol, name, coingecko_id FROM t_assets WHERE symbol = 'DJED' OR name ILIKE '%djed%'")
rows = cur.fetchall()

if not rows:
    print("❌ DJED não encontrado na base de dados!")
    print("Vou inserir DJED com coingecko_id...")
    
    # Inserir DJED
    cur.execute(
        """
        INSERT INTO t_assets (symbol, name, chain, coingecko_id, is_stablecoin)
        VALUES ('DJED', 'DJED', 'Cardano', 'djed', true)
        ON CONFLICT (symbol) DO UPDATE SET coingecko_id = 'djed', is_stablecoin = true
        """
    )
    conn.commit()
    print("✅ DJED inserido/atualizado")
    
    # Re-query
    cur.execute("SELECT asset_id, symbol, name, coingecko_id FROM t_assets WHERE symbol = 'DJED'")
    rows = cur.fetchall()
else:
    print(f"✅ DJED encontrado:")
    for row in rows:
        print(f"  asset_id={row[0]}, symbol={row[1]}, name={row[2]}, coingecko_id={row[3]}")

djed_coingecko_id = rows[0][3] if rows else None

print("\n" + "=" * 60)
print("2. Verificando DjedMicroUSD (6df63e2f...)...")
print("=" * 60)

# 2. Verificar se DjedMicroUSD existe
cur.execute(
    """
    SELECT asset_id, symbol, name, coingecko_id 
    FROM t_assets 
    WHERE symbol LIKE '%6df63e2f%' OR name = 'DjedMicroUSD' OR symbol = 'DjedMicroUSD'
    """
)
rows_micro = cur.fetchall()

if not rows_micro:
    print("❌ DjedMicroUSD não encontrado")
else:
    print(f"✅ DjedMicroUSD encontrado:")
    for row in rows_micro:
        print(f"  asset_id={row[0]}, symbol={row[1]}, name={row[2]}, coingecko_id={row[3]}")

# 3. Verificar na t_cardano_assets
print("\n" + "=" * 60)
print("3. Verificando t_cardano_assets...")
print("=" * 60)

cur.execute(
    """
    SELECT policy_id, asset_name_hex, display_name, decimals 
    FROM t_cardano_assets 
    WHERE policy_id LIKE '6df63e2f%' OR display_name ILIKE '%djed%'
    ORDER BY display_name
    """
)
rows_cardano = cur.fetchall()

if not rows_cardano:
    print("❌ Nenhum asset Djed encontrado em t_cardano_assets")
else:
    print(f"✅ Assets Djed em t_cardano_assets:")
    for row in rows_cardano:
        print(f"  policy_id={row[0][:16]}..., asset_name_hex={row[1]}, display_name={row[2]}, decimals={row[3]}")

# 4. Atualizar/inserir DjedMicroUSD com coingecko_id do DJED
print("\n" + "=" * 60)
print("4. Configurando DjedMicroUSD para usar preço do DJED...")
print("=" * 60)

if djed_coingecko_id:
    # Inserir/atualizar DjedMicroUSD com o policy_id completo como símbolo
    cur.execute(
        """
        INSERT INTO t_assets (symbol, name, chain, coingecko_id, is_stablecoin)
        VALUES ('6df63e2fdde8b2c3b3396265b0cc824aa4fb999396b1c154280f6b0c', 'DjedMicroUSD', 'Cardano', %s, true)
        ON CONFLICT (symbol) DO UPDATE 
        SET coingecko_id = EXCLUDED.coingecko_id, 
            name = EXCLUDED.name,
            is_stablecoin = EXCLUDED.is_stablecoin
        """,
        (djed_coingecko_id,)
    )
    
    # Também criar um alias mais legível
    cur.execute(
        """
        INSERT INTO t_assets (symbol, name, chain, coingecko_id, is_stablecoin)
        VALUES ('DjedMicroUSD', 'DjedMicroUSD (Liqwid Receipt)', 'Cardano', %s, true)
        ON CONFLICT (symbol) DO UPDATE 
        SET coingecko_id = EXCLUDED.coingecko_id,
            name = EXCLUDED.name,
            is_stablecoin = EXCLUDED.is_stablecoin
        """,
        (djed_coingecko_id,)
    )
    
    conn.commit()
    print(f"✅ DjedMicroUSD configurado com coingecko_id = '{djed_coingecko_id}'")
else:
    print("❌ Não foi possível configurar - DJED sem coingecko_id")

# 5. Verificar resultado
print("\n" + "=" * 60)
print("5. Verificação final...")
print("=" * 60)

cur.execute(
    """
    SELECT asset_id, symbol, name, coingecko_id, is_stablecoin 
    FROM t_assets 
    WHERE symbol IN ('DJED', 'DjedMicroUSD', '6df63e2fdde8b2c3b3396265b0cc824aa4fb999396b1c154280f6b0c')
    ORDER BY symbol
    """
)
rows_final = cur.fetchall()

for row in rows_final:
    symbol_display = row[1][:20] + "..." if len(row[1]) > 20 else row[1]
    print(f"  asset_id={row[0]}, symbol={symbol_display}, name={row[2]}, coingecko_id={row[3]}, stablecoin={row[4]}")

return_connection(conn)

print("\n" + "=" * 60)
print("✅ Script concluído!")
print("=" * 60)
print("\nAgora você pode:")
print("1. Ir a Settings → Snapshots e preencher preços para DJED")
print("2. O DjedMicroUSD vai usar automaticamente o preço do DJED")
print("3. Voltar ao Portfolio v3 e atualizar a página")
