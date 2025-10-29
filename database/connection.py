import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
from contextlib import contextmanager

# Carrega variáveis do .env
load_dotenv()

# Connection pool for better performance
_connection_pool = None


def _get_pool():
    """Get or create the connection pool."""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
    return _connection_pool


def get_connection():
    """Get a connection from the pool."""
    pool_obj = _get_pool()
    return pool_obj.getconn()


def return_connection(conn):
    """Return a connection to the pool."""
    pool_obj = _get_pool()
    pool_obj.putconn(conn)


@contextmanager
def get_db_cursor():
    """Context manager for database operations.
    
    Usage:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM table")
            results = cur.fetchall()
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        return_connection(conn)


def get_db_connection():
    """Backward-compatible alias used across the codebase.

    Some modules import `get_db_connection` while older code used `get_connection`.
    This helper ensures both names work.
    """
    return get_connection()
