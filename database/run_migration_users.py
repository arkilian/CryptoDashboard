"""
Script para executar migration: adicionar created_at na tabela t_users
"""
from database.connection import get_connection, return_connection
import os

def run_migration():
    migration_file = os.path.join(os.path.dirname(__file__), 'migrations', 'add_created_at_to_users.sql')
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # Execute migration
        cur.execute(sql)
        conn.commit()
        
        print("✅ Migration executada com sucesso!")
        print("✅ Coluna 'created_at' adicionada à tabela t_users")
        
        # Verificar resultado
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 't_users'")
        columns = [row[0] for row in cur.fetchall()]
        print(f"\n📋 Colunas da tabela t_users: {', '.join(columns)}")
        
        cur.close()
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao executar migration: {e}")
        raise
    finally:
        return_connection(conn)

if __name__ == "__main__":
    run_migration()
