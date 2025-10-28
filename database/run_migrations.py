import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

def run_migrations():
    """
    Executa todos os scripts SQL na pasta migrations em ordem alfabética
    """
    load_dotenv()
    
    # Conectar ao banco de dados
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    cursor = conn.cursor()

    try:
        # Criar tabela de controle de migrações se não existir
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS t_migrations (
                migration_id SERIAL PRIMARY KEY,
                migration_name TEXT UNIQUE NOT NULL,
                executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Listar migrações já executadas
        cursor.execute("SELECT migration_name FROM t_migrations")
        executed_migrations = {row[0] for row in cursor.fetchall()}
        
        # Listar arquivos .sql na pasta migrations
        migrations_dir = Path(__file__).parent / "migrations"
        migration_files = sorted(migrations_dir.glob("*.sql"))
        
        for migration_file in migration_files:
            migration_name = migration_file.name
            
            if migration_name in executed_migrations:
                print(f"Skipping {migration_name} - already executed")
                continue
            
            print(f"Executing {migration_name}...")
            
            # Ler e executar o script SQL
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql = f.read()
                cursor.execute(sql)
            
            # Registrar migração como executada
            cursor.execute(
                "INSERT INTO t_migrations (migration_name) VALUES (%s)",
                (migration_name,)
            )
            
            print(f"Successfully executed {migration_name}")
        
        conn.commit()
        print("All migrations completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error executing migrations: {str(e)}")
        raise
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_migrations()