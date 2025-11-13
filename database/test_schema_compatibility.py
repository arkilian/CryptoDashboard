"""
Script para testar a compatibilidade entre schema.sql e data_export.sql
Verifica se todas as colunas dos INSERTs existem no schema
"""
import re
import sys
from pathlib import Path

def extract_schema_columns(schema_file):
    """Extrai as colunas de cada tabela do schema.sql"""
    with open(schema_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tables = {}
    current_table = None
    in_table_def = False
    
    for line in content.split('\n'):
        # Detectar início de tabela
        match = re.match(r'CREATE TABLE IF NOT EXISTS (\w+) \(', line)
        if match:
            current_table = match.group(1)
            tables[current_table] = []
            in_table_def = True
            continue
        
        # Detectar fim de tabela
        if in_table_def and ');' in line:
            in_table_def = False
            current_table = None
            continue
        
        # Extrair colunas
        if in_table_def and current_table:
            col_match = re.match(r'\s+(\w+)\s+', line)
            if col_match and not line.strip().startswith('--'):
                col_name = col_match.group(1)
                # Ignorar constraints
                if col_name.upper() not in ['UNIQUE', 'PRIMARY', 'FOREIGN', 'CHECK', 'CONSTRAINT']:
                    tables[current_table].append(col_name)
    
    return tables

def extract_insert_columns(data_file):
    """Extrai as colunas usadas nos INSERTs do data_export.sql"""
    with open(data_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    inserts = {}
    
    # Encontrar todos os INSERTs
    pattern = r'INSERT INTO (\w+) \((.*?)\)'
    matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
    
    for match in matches:
        table = match.group(1)
        columns_str = match.group(2)
        
        # Limpar e separar colunas
        columns = [col.strip() for col in columns_str.replace('\n', ' ').split(',')]
        
        if table not in inserts:
            inserts[table] = set()
        inserts[table].update(columns)
    
    return inserts

def main():
    base_dir = Path(__file__).parent
    schema_file = base_dir / 'schema.sql'
    data_file = base_dir / 'data_export.sql'
    
    if not schema_file.exists():
        print(f"❌ Ficheiro não encontrado: {schema_file}")
        sys.exit(1)
    
    if not data_file.exists():
        print(f"❌ Ficheiro não encontrado: {data_file}")
        sys.exit(1)
    
    print("=" * 70)
    print("TESTE DE COMPATIBILIDADE: SCHEMA vs DATA EXPORT")
    print("=" * 70)
    print()
    
    # Extrair informação
    schema_tables = extract_schema_columns(schema_file)
    insert_tables = extract_insert_columns(data_file)
    
    print(f"📋 Tabelas no schema: {len(schema_tables)}")
    print(f"📊 Tabelas com dados: {len(insert_tables)}")
    print()
    
    # Verificar compatibilidade
    errors = []
    warnings = []
    
    for table, insert_cols in insert_tables.items():
        if table not in schema_tables:
            warnings.append(f"⚠️  Tabela '{table}' tem dados mas não existe no schema")
            continue
        
        schema_cols = set(schema_tables[table])
        missing_cols = insert_cols - schema_cols
        
        if missing_cols:
            errors.append(f"❌ Tabela '{table}': colunas faltam no schema: {', '.join(missing_cols)}")
        else:
            print(f"✓ {table}: OK ({len(insert_cols)} colunas)")
    
    print()
    print("=" * 70)
    
    if errors:
        print("❌ ERROS ENCONTRADOS:")
        print()
        for error in errors:
            print(error)
        print()
        sys.exit(1)
    
    if warnings:
        print("⚠️  AVISOS:")
        print()
        for warning in warnings:
            print(warning)
        print()
    
    print("✅ COMPATIBILIDADE: OK")
    print("   Todas as colunas dos INSERTs existem no schema!")
    print("=" * 70)
    print()

if __name__ == '__main__':
    main()
