"""
Script para exportar dados existentes da base de dados para ficheiro SQL de INSERT's
"""
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Conexão à base de dados
conn = psycopg2.connect(
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT')
)

def format_value(val):
    """Formata um valor para SQL"""
    if val is None:
        return 'NULL'
    elif isinstance(val, bool):
        return 'TRUE' if val else 'FALSE'
    elif isinstance(val, (int, float)):
        return str(val)
    elif isinstance(val, datetime):
        return f"'{val.isoformat()}'"
    else:
        # Escape aspas simples
        val_str = str(val).replace("'", "''")
        return f"'{val_str}'"

def export_table_data(cursor, table_name, output_file):
    """Exporta dados de uma tabela para ficheiro SQL"""
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        if count == 0:
            output_file.write(f"\n-- Tabela {table_name}: sem dados\n")
            return
        
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        if not rows:
            output_file.write(f"\n-- Tabela {table_name}: sem dados\n")
            return
        
        # Obter nomes das colunas
        col_names = [desc[0] for desc in cursor.description]
        
        output_file.write(f"\n-- ========================================\n")
        output_file.write(f"-- DADOS DA TABELA: {table_name}\n")
        output_file.write(f"-- Total de registos: {count}\n")
        output_file.write(f"-- ========================================\n\n")
        
        for row in rows:
            values = [format_value(val) for val in row]
            columns = ', '.join(col_names)
            values_str = ', '.join(values)
            
            output_file.write(f"INSERT INTO {table_name} ({columns})\n")
            output_file.write(f"VALUES ({values_str})\n")
            output_file.write(f"ON CONFLICT DO NOTHING;\n\n")
        
        print(f"✓ Exportados {count} registos de {table_name}")
    
    except Exception as e:
        output_file.write(f"\n-- ERRO ao exportar {table_name}: {str(e)}\n")
        print(f"✗ Erro ao exportar {table_name}: {str(e)}")

# Ordem de exportação (respeitando dependências de chaves estrangeiras)
TABLES_ORDER = [
    # Tabelas base sem dependências
    't_gender',
    't_users',
    't_exchanges',
    't_assets',
    't_fee_settings',
    't_tags',
    
    # Tabelas com dependências de nível 1
    't_address',
    't_user_profile',
    't_exchange_accounts',
    't_user_high_water',
    't_wallet',
    't_banco',
    't_api_coingecko',
    't_api_cardano',
    't_cardano_assets',
    
    # Tabelas com dependências de nível 2+
    't_user_capital_movements',
    't_transactions',
    't_price_snapshots',
    't_portfolio_snapshots',
    't_portfolio_holdings',
    't_user_snapshots',
    't_user_manual_snapshots',
    't_snapshot_assets',
    't_transaction_tags',
    't_user_shares',
    't_user_fees',
    
    # Tabelas Cardano
    't_cardano_transactions',
    't_cardano_tx_io',
]

def main():
    output_filename = 'c:/CryptoDashboard/database/data_export.sql'
    
    print(f"\n{'='*60}")
    print("EXPORTAÇÃO DE DADOS DA BASE DE DADOS")
    print(f"{'='*60}\n")
    print(f"Base de dados: {os.getenv('DB_NAME')}")
    print(f"Ficheiro de saída: {output_filename}\n")
    
    cursor = conn.cursor()
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        # Cabeçalho
        f.write("-- ========================================\n")
        f.write("-- CRYPTO DASHBOARD - DADOS EXISTENTES\n")
        f.write("-- ========================================\n")
        f.write(f"-- Exportado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"-- Base de dados: {os.getenv('DB_NAME')}\n")
        f.write("-- ========================================\n")
        f.write("-- INSTRUÇÕES:\n")
        f.write("-- 1. Criar a base de dados com: schema.sql\n")
        f.write("-- 2. Importar os dados com: psql -U <user> -d <dbname> -f data_export.sql\n")
        f.write("-- ========================================\n\n")
        
        f.write("-- Desabilitar triggers durante importação\n")
        f.write("SET session_replication_role = replica;\n\n")
        
        # Exportar cada tabela
        for table_name in TABLES_ORDER:
            export_table_data(cursor, table_name, f)
        
        f.write("\n-- Reabilitar triggers\n")
        f.write("SET session_replication_role = DEFAULT;\n\n")
        
        f.write("-- ========================================\n")
        f.write("-- FIM DA EXPORTAÇÃO\n")
        f.write("-- ========================================\n")
    
    cursor.close()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✓ Exportação concluída com sucesso!")
    print(f"✓ Ficheiro criado: {output_filename}")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
