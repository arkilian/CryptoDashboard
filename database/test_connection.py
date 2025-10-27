from connection import get_connection
import psycopg2

try:
    conn = get_connection()
    print("Conexão estabelecida com sucesso!")
    conn.close()
except psycopg2.Error as e:
    print(f"Erro ao conectar: {e}")
