#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verificar dados importados do CSV na base de dados."""
import sys
from pathlib import Path

# Adicionar root ao path para imports funcionarem
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


from database.connection import get_engine
from sqlalchemy import text

engine = get_engine()

with engine.connect() as conn:
    # ADA snapshots do CSV
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total,
            MIN(snapshot_date) as min_date,
            MAX(snapshot_date) as max_date,
            AVG(price_eur) as avg_price,
            MIN(price_eur) as min_price,
            MAX(price_eur) as max_price
        FROM t_price_snapshots 
        WHERE asset_id = 4 AND source = 'coingecko_csv'
    """)).fetchone()
    
    print(f"📊 ADA Snapshots (CSV import)")
    print(f"   Total: {result[0]} registos")
    print(f"   Período: {result[1]} a {result[2]}")
    print(f"   Preço médio: €{result[3]:.4f}")
    print(f"   Preço mín: €{result[4]:.6f}")
    print(f"   Preço máx: €{result[5]:.4f}")
    
    # Comparar com snapshots da API
    result2 = conn.execute(text("""
        SELECT COUNT(*) as total
        FROM t_price_snapshots 
        WHERE asset_id = 4 AND source != 'coingecko_csv'
    """)).fetchone()
    
    print(f"\n📊 ADA Snapshots (API)")
    print(f"   Total: {result2[0]} registos")
    
    # Total geral
    result3 = conn.execute(text("""
        SELECT COUNT(DISTINCT snapshot_date) as unique_dates
        FROM t_price_snapshots 
        WHERE asset_id = 4
    """)).fetchone()
    
    print(f"\n📊 ADA Snapshots (Total)")
    print(f"   Datas únicas: {result3[0]}")
