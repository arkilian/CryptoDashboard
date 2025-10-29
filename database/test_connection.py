from connection import get_connection, return_connection
import psycopg2

try:
    conn = get_connection()
    print("Conexão estabelecida com sucesso!")
    # Devolve a ligação ao pool
    return_connection(conn)
except psycopg2.Error as e:
    print(f"Erro ao conectar: {e}")
